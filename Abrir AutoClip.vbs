Option Explicit
Dim files, shell, root, python, command
Set files = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
root = files.GetParentFolderName(WScript.ScriptFullName)
python = files.BuildPath(root, ".venv\Scripts\pythonw.exe")
If Not files.FileExists(python) Then
  MsgBox "O ambiente local do AutoClip não foi encontrado. Reinstale a versão local do projeto.", 16, "AutoClip"
  WScript.Quit 1
End If
shell.CurrentDirectory = root
command = Chr(34) & python & Chr(34) & " -X utf8 -m engine.api.launcher " & Chr(34) & root & Chr(34)
shell.Run command, 0, False
