use crate::supervisor::{workspace, Supervisor};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};
use tauri::{WebviewUrl, WebviewWindowBuilder, WindowEvent};

fn background_notice() {
    #[cfg(windows)]
    unsafe {
        use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONINFORMATION, MB_OK};
        let text: Vec<u16> =
            "O processamento continua em segundo plano. Abra AutoClip novamente para acompanhar.\0"
                .encode_utf16()
                .collect();
        let title: Vec<u16> = "AutoClip\0".encode_utf16().collect();
        MessageBoxW(
            std::ptr::null_mut(),
            text.as_ptr(),
            title.as_ptr(),
            MB_OK | MB_ICONINFORMATION,
        );
    }
}
pub fn run() {
    tauri::Builder::default().setup(|app|{
        let loading=WebviewWindowBuilder::new(app,"startup",WebviewUrl::App("startup.html".into())).title("AutoClip — Iniciando").inner_size(720.,440.).background_color(tauri::window::Color(16,19,22,255)).build()?;
        let handle=app.handle().clone();
        std::thread::spawn(move||{
            let result=workspace().and_then(|root|Supervisor::start(&root));
            match result {
                Ok((supervisor,session))=>{
                    let origin=session.origin.clone();let download_origin=origin.clone();let _owned=session.owned;
                    let token=serde_json::to_string(&format!("session={}",session.token)).unwrap();
                    let supervisor=Arc::new(Mutex::new(supervisor));
                    let closing=Arc::new(AtomicBool::new(false));
                    let main=WebviewWindowBuilder::new(&handle,"main",WebviewUrl::External(session.origin.parse().unwrap()))
                        .title("AutoClip").inner_size(1440.,900.).min_inner_size(1000.,680.)
                        .background_color(tauri::window::Color(16,19,22,255))
                        .initialization_script(format!("if(location.origin==={}){{location.hash={};}}",serde_json::to_string(&origin).unwrap(),token))
                        .on_navigation(move|url|url.origin().ascii_serialization()==origin)
                        .on_new_window(|_,_|tauri::webview::NewWindowResponse::Deny)
                        .on_download(move|_,event|match event {tauri::webview::DownloadEvent::Requested{url,..}=>url.origin().ascii_serialization()==download_origin,_=>true})
                        .build();
                    match main {
                        Ok(main)=>{
                            let window=main.clone();let exit_handle=handle.clone();
                            main.on_window_event(move|event|if let WindowEvent::CloseRequested{api,..}=event{
                                api.prevent_close();if closing.swap(true,Ordering::SeqCst){return;}
                                let worker=supervisor.clone();let window=window.clone();let handle=exit_handle.clone();
                                std::thread::spawn(move||{let result=worker.lock().unwrap().close();if result=="busy"{background_notice();}let _=window.destroy();handle.exit(0);});
                            });
                            let _=loading.destroy();
                        },
                        Err(_)=>{let _=loading.eval("document.getElementById('status').textContent='Não foi possível abrir a janela. Tente novamente.'");}
                    }
                },
                Err(message)=>{let _=loading.eval(&format!("document.getElementById('status').textContent={}",serde_json::to_string(&message).unwrap()));}
            }
        });Ok(())
    }).run(tauri::generate_context!()).expect("Falha ao iniciar a janela AutoClip");
}
