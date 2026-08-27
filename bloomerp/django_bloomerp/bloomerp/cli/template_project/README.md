# __PROJECT_NAME__

This project was created with `bloomerp project init`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python manage.py migrate
python manage.py createsuperuser
python manage.py save_application_fields
python manage.py runserver
```

## Project configuration

- Add dependencies to `pyproject.toml`.
- Register Django applications in `.bloomerp/project.toml`.
- Put shared custom settings in `config/settings/common.py`.
- Put environment-specific overrides in `local.py` or `production.py`.
- Put custom URLs in `config/project_urls.py`.

Run `bloomerp project scaffold-sync` after upgrading Bloomerp. Generated files
under `config/settings/generated/` may be replaced; project-owned files are
never overwritten.
