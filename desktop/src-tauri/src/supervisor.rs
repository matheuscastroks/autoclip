use serde::Deserialize;
use std::{
    io::{BufRead, BufReader, Read, Write},
    path::{Path, PathBuf},
    process::{Child, ChildStdin, ChildStdout, Command, Stdio},
};
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Session {
    pub schema_version: String,
    pub origin: String,
    pub token: String,
    pub owned: bool,
}
pub fn valid_origin(value: &str) -> bool {
    url::Url::parse(value)
        .map(|u| {
            u.scheme() == "http"
                && u.host_str() == Some("127.0.0.1")
                && u.port().is_some_and(|p| p >= 1024)
                && u.username().is_empty()
                && u.password().is_none()
                && u.path() == "/"
                && u.query().is_none()
                && u.fragment().is_none()
        })
        .unwrap_or(false)
}
pub fn parse_session(line: &str) -> Result<Session, String> {
    let session: Session = serde_json::from_str(line)
        .map_err(|_| "O motor não iniciou. Confira .autoclip/server.log.")?;
    if session.schema_version != "1.0"
        || !valid_origin(&session.origin)
        || session.token.len() < 16
        || session.token.len() > 128
        || !session
            .token
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b == b'-' || b == b'_')
    {
        return Err("Sessão local inválida.".into());
    }
    Ok(session)
}
pub fn workspace() -> Result<PathBuf, String> {
    if let Some(path) = std::env::var_os("AUTOCLIP_WORKSPACE") {
        return Ok(PathBuf::from(path));
    }
    let executable =
        std::env::current_exe().map_err(|_| "Não foi possível localizar o aplicativo.")?;
    for dir in executable.ancestors() {
        if dir.join("engine/api/server.py").is_file()
            && dir.join(".venv/Scripts/python.exe").is_file()
        {
            return Ok(dir.to_path_buf());
        }
    }
    Err("Abra o aplicativo dentro do checkout ou configure AUTOCLIP_WORKSPACE.".into())
}
pub struct Supervisor {
    child: Child,
    input: ChildStdin,
    output: BufReader<ChildStdout>,
}
impl Supervisor {
    pub fn start(root: &Path) -> Result<(Self, Session), String> {
        let python = root.join(".venv/Scripts/python.exe");
        let mut command = Command::new(python);
        command
            .args(["-X", "utf8", "-m", "engine.api.desktop_session"])
            .arg(root)
            .current_dir(root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null());
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x08000000);
        }
        let mut child = command
            .spawn()
            .map_err(|_| "Não foi possível iniciar Python. Confira o ambiente local.")?;
        let input = child.stdin.take().ok_or("Canal do motor indisponível.")?;
        let output = BufReader::new(
            child
                .stdout
                .take()
                .ok_or("Resposta do motor indisponível.")?,
        );
        let mut supervisor = Self {
            child,
            input,
            output,
        };
        let mut line = String::new();
        supervisor
            .output
            .by_ref()
            .take(65536)
            .read_line(&mut line)
            .map_err(|_| "O motor não respondeu.")?;
        let session = parse_session(&line)?;
        Ok((supervisor, session))
    }
    pub fn close(&mut self) -> String {
        if self
            .input
            .write_all(b"close\n")
            .and_then(|_| self.input.flush())
            .is_err()
        {
            return "unavailable".into();
        }
        let mut line = String::new();
        if self
            .output
            .by_ref()
            .take(65536)
            .read_line(&mut line)
            .is_err()
        {
            return "unavailable".into();
        }
        let response: serde_json::Value = serde_json::from_str(&line).unwrap_or_default();
        let _ = self.child.wait();
        response["result"]
            .as_str()
            .unwrap_or("unavailable")
            .to_string()
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn rejects_invalid_private_protocol() {
        assert!(parse_session("{\"error\":\"startup failure\"}").is_err());
        assert!(parse_session("{broken").is_err());
        let valid = serde_json::json!({"schema_version":"1.0","origin":"http://127.0.0.1:8765","token":"fixture-token-123456","owned":false});
        assert!(parse_session(&valid.to_string()).is_ok());
        let mut invalid = valid;
        invalid["token"] = serde_json::json!("short");
        assert!(parse_session(&invalid.to_string()).is_err());
    }
    #[test]
    fn rejects_non_loopback() {
        for s in [
            "https://127.0.0.1:8765",
            "http://localhost:8765",
            "http://127.0.0.1:80",
            "http://127.0.0.1:8765/?token=x",
            "http://x@127.0.0.1:8765",
        ] {
            assert!(!valid_origin(s));
        }
        assert!(valid_origin("http://127.0.0.1:8765"));
    }
}
