"""Remove disposable history while retaining jobs that can still be resumed."""
import shutil
from pathlib import Path

DISPOSABLE = ('completed', 'rejected')
RESUMABLE = ('failed', 'cancelled', 'interrupted')


def clear_job_history(store, jobs_root: Path, owned_alive):
    root = jobs_root.resolve()
    cleared = preserved = 0
    errors = []
    for job in store.jobs():
        if job['status'] not in DISPOSABLE:
            preserved += job['status'] in RESUMABLE
            continue
        if owned_alive(job):
            preserved += 1
            continue
        folder = jobs_root / job['id']
        # Never follow a symlink or an identifier outside the jobs directory.
        if folder.is_symlink() or folder.resolve().parent != root:
            errors.append({'job_id': job['id'], 'message': 'Diretório de tarefa inválido; dados preservados.'})
            continue
        try:
            if folder.exists():
                shutil.rmtree(folder)
            if folder.exists():
                raise OSError('Job directory was not removed')
        except OSError:
            errors.append({'job_id': job['id'], 'message': 'Não foi possível limpar os arquivos desta tarefa. Tente novamente.'})
            continue
        cleared += store.delete_finished_job(job['id'])
    return {'cleared': cleared, 'preserved': preserved, 'errors': errors}
