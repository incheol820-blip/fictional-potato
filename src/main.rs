use std::fs;
use std::path::{Path, PathBuf};

use anyhow::Context;
use chrono::{DateTime, Utc};
use eframe::{egui, App};
use serde::Deserialize;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default().with_inner_size([1100.0, 720.0]),
        ..Default::default()
    };

    eframe::run_native(
        "Codex Session Viewer",
        options,
        Box::new(|cc| {
            configure_fonts(&cc.egui_ctx);
            Ok(Box::new(SessionViewerApp::new()))
        }),
    )
}

fn configure_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    #[cfg(target_os = "windows")]
    {
        // Windows 기본 한글 폰트 (맑은 고딕) 우선 사용
        let malgun_path = Path::new(r"C:\Windows\Fonts\malgun.ttf");
        if let Ok(bytes) = fs::read(malgun_path) {
            fonts
                .font_data
                .insert("malgun_gothic".to_owned(), egui::FontData::from_owned(bytes).into());

            if let Some(family) = fonts.families.get_mut(&egui::FontFamily::Proportional) {
                family.insert(0, "malgun_gothic".to_owned());
            }
            if let Some(family) = fonts.families.get_mut(&egui::FontFamily::Monospace) {
                family.insert(0, "malgun_gothic".to_owned());
            }
        }
    }

    ctx.set_fonts(fonts);
}

#[derive(Clone, Debug)]
struct SessionSummary {
    id: String,
    title: String,
    updated_at: Option<DateTime<Utc>>,
    turns: Vec<Turn>,
    file_path: PathBuf,
}

#[derive(Clone, Debug, Deserialize)]
struct Turn {
    role: String,
    content: String,
}

#[derive(Debug, Deserialize)]
struct SessionFile {
    id: Option<String>,
    title: Option<String>,
    updated_at: Option<DateTime<Utc>>,
    turns: Option<Vec<Turn>>,
}

struct SessionViewerApp {
    sessions: Vec<SessionSummary>,
    selected_idx: usize,
    last_error: Option<String>,
    session_dir: PathBuf,
}

impl SessionViewerApp {
    fn new() -> Self {
        let session_dir = detect_session_dir();
        let mut app = Self {
            sessions: vec![],
            selected_idx: 0,
            last_error: None,
            session_dir,
        };
        app.reload();
        app
    }

    fn reload(&mut self) {
        match load_sessions(&self.session_dir) {
            Ok(sessions) => {
                self.sessions = sessions;
                if self.selected_idx >= self.sessions.len() {
                    self.selected_idx = self.sessions.len().saturating_sub(1);
                }
                self.last_error = None;
            }
            Err(e) => {
                self.sessions.clear();
                self.selected_idx = 0;
                self.last_error = Some(e.to_string());
            }
        }
    }

    fn selected_session(&self) -> Option<&SessionSummary> {
        self.sessions.get(self.selected_idx)
    }
}

impl App for SessionViewerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        if ctx.input(|i| i.key_pressed(egui::Key::ArrowDown)) && self.selected_idx + 1 < self.sessions.len() {
            self.selected_idx += 1;
        }
        if ctx.input(|i| i.key_pressed(egui::Key::ArrowUp)) && self.selected_idx > 0 {
            self.selected_idx -= 1;
        }

        egui::TopBottomPanel::top("toolbar").show(ctx, |ui| {
            ui.horizontal(|ui| {
                ui.heading("Codex Session Viewer");
                if ui.button("Reload").clicked() {
                    self.reload();
                }
                ui.separator();
                ui.label(format!("Session path: {}", self.session_dir.display()));
            });
        });

        egui::SidePanel::left("session_list").resizable(true).show(ctx, |ui| {
            ui.heading(format!("Sessions ({})", self.sessions.len()));
            ui.label("↑/↓ 키로 이동, 클릭/Enter로 선택");
            ui.separator();

            egui::ScrollArea::vertical().show(ui, |ui| {
                for (idx, session) in self.sessions.iter().enumerate() {
                    let label = format!(
                        "{}{}",
                        session.title,
                        session
                            .updated_at
                            .map(|d| format!("  ({})", d.format("%Y-%m-%d %H:%M")))
                            .unwrap_or_default()
                    );

                    let resp = ui.selectable_label(idx == self.selected_idx, label);
                    if resp.clicked() {
                        self.selected_idx = idx;
                    }
                }
            });
        });

        egui::CentralPanel::default().show(ctx, |ui| {
            if let Some(err) = &self.last_error {
                ui.colored_label(egui::Color32::RED, format!("Load error: {err}"));
            }

            if let Some(session) = self.selected_session() {
                ui.heading(&session.title);
                ui.label(format!("Session ID: {}", session.id));
                ui.label(format!("File: {}", session.file_path.display()));
                if let Some(ts) = session.updated_at {
                    ui.label(format!("Updated: {}", ts.format("%Y-%m-%d %H:%M:%S UTC")));
                }
                ui.separator();

                ui.label("대화 미리보기");
                egui::ScrollArea::vertical().auto_shrink([false; 2]).show(ui, |ui| {
                    for turn in &session.turns {
                        ui.group(|ui| {
                            ui.strong(turn.role.to_uppercase());
                            ui.label(&turn.content);
                        });
                    }
                });
            } else {
                ui.label("세션이 없습니다. 세션 디렉터리를 확인해주세요.");
            }
        });
    }
}

fn detect_session_dir() -> PathBuf {
    if let Ok(path) = std::env::var("CODEX_SESSION_DIR") {
        return PathBuf::from(path);
    }

    if let Some(home) = dirs::home_dir() {
        return home.join(".codex").join("sessions");
    }

    PathBuf::from("sessions")
}

fn load_sessions(base_dir: &Path) -> anyhow::Result<Vec<SessionSummary>> {
    let mut out = Vec::new();

    if !base_dir.exists() {
        return Ok(out);
    }

    for entry in fs::read_dir(base_dir).with_context(|| format!("Cannot read {}", base_dir.display()))? {
        let entry = entry?;
        let path = entry.path();
        if path.extension().and_then(|s| s.to_str()) != Some("json") {
            continue;
        }

        // Rust 문자열/파일 파싱은 UTF-8 기반. fs::read_to_string + serde_json 조합으로
        // 세션 내 한글 텍스트를 그대로 유지해 UI까지 전달합니다.
        let raw = fs::read_to_string(&path)
            .with_context(|| format!("Failed to read {}", path.display()))?;

        let session: SessionFile = match serde_json::from_str(&raw) {
            Ok(v) => v,
            Err(_) => continue,
        };

        let turns = session.turns.unwrap_or_default();
        let title = session
            .title
            .unwrap_or_else(|| summarize_title(&turns).unwrap_or_else(|| "Untitled Session".to_string()));
        let id = session.id.unwrap_or_else(|| {
            path.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("unknown")
                .to_string()
        });

        out.push(SessionSummary {
            id,
            title,
            updated_at: session.updated_at,
            turns,
            file_path: path,
        });
    }

    out.sort_by_key(|s| s.updated_at);
    out.reverse();

    Ok(out)
}

fn summarize_title(turns: &[Turn]) -> Option<String> {
    turns
        .iter()
        .find(|t| t.role.eq_ignore_ascii_case("user"))
        .map(|t| {
            let mut text = t.content.replace('\n', " ");
            if text.chars().count() > 48 {
                text = text.chars().take(48).collect::<String>() + "…";
            }
            text
        })
}
