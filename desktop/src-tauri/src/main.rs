#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]
mod supervisor;
mod window;
fn main() {
    window::run();
}
