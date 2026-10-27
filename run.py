from app import create_app, db
from app.models import User, Role, Project, ProjectMember, Milestone

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Project': Project,
        'ProjectMember': ProjectMember,
        'Milestone': Milestone,
    }


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
