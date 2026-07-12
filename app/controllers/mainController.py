from flask import render_template


def landing_page():
    featured_projects = [
        {
            "title": "Earthbound Identity",
            "creator": "Maya Studio",
            "category": "Graphic Design",
            "accent": "coral",
        },
        {
            "title": "Quiet Architecture",
            "creator": "Arun Frames",
            "category": "Photography",
            "accent": "blue",
        },
        {
            "title": "Lumen Mobile",
            "creator": "Sofia UX",
            "category": "UI/UX Design",
            "accent": "lime",
        },
    ]
    featured_creators = [
        {"name": "Maya Shrestha", "profession": "Brand Designer", "initials": "MS"},
        {"name": "Arun Rai", "profession": "Photographer", "initials": "AR"},
        {"name": "Sofia Chen", "profession": "Product Designer", "initials": "SC"},
    ]
    return render_template(
        "landing.html",
        featured_projects=featured_projects,
        featured_creators=featured_creators,
    )
