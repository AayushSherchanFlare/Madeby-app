import re
from datetime import datetime
from pathlib import Path


def active_user():
    return {
        "user_id": 7,
        "full_name": "Arun Rai",
        "username": "arun",
        "email": "arun@example.com",
        "profession": "Designer",
        "biography": "I make useful things.",
        "website_url": "https://example.com",
        "profile_image": None,
        "cover_image": None,
        "role": "user",
        "account_status": "active",
        "unread_notification_count": 3,
    }


def log_in(client):
    with client.session_transaction() as session:
        session["user_id"] = 7
        session["role"] = "user"


def test_dashboard_mobile_layout_cannot_retain_desktop_sidebar_column():
    project_root = Path(__file__).resolve().parents[1]
    css = (project_root / "app" / "static" / "css" / "dashboard.css").read_text(
        encoding="utf-8"
    )
    base_template = (project_root / "app" / "templates" / "base.html").read_text(
        encoding="utf-8"
    )

    assert "@media (max-width: 1040px), (max-device-width: 1040px) {" in css
    assert '@media (max-width: 1040px), (hover: none), (pointer: coarse)' not in css
    assert "grid-template-columns: minmax(0, 1fr);" in css
    assert "var(--madeby-visible-width, 100vw)" in css
    assert ".dashboard-body {\n  min-height: 100vh;\n  overflow-x: clip;" in css
    assert ".profile-identity { min-width: 0;" in css
    assert "viewport-fit=cover" in base_template
    assert "window.visualViewport?.width" in base_template
    assert "window.visualViewport?.height" in base_template
    assert "window.screen?.width" in base_template
    assert "--madeby-visible-height" in base_template
    assert 'window.addEventListener("pageshow", syncVisibleViewport)' in base_template
    assert "top: calc(var(--madeby-visible-height, 100dvh) - 66px);" in css


def install_user(monkeypatch):
    monkeypatch.setattr(
        "app.repository.userRepository.find_by_id",
        lambda _user_id: active_user(),
    )


def test_feed_requires_login(client):
    response = client.get("/feed")

    assert response.status_code == 302
    assert "/login?next=/feed" in response.headers["Location"]


def test_feed_renders_posts_and_discovery(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_feed",
        lambda _user_id, category_id=None: [
            {
                "project_id": 12,
                "user_id": 8,
                "title": None,
                "description": "A new poster design.",
                "cover_image": None,
                "created_at": datetime(2026, 7, 24),
                "full_name": "Maya Shrestha",
                "username": "maya",
                "profession": "Illustrator",
                "profile_image": None,
                "category_name": "Graphic Design",
                "like_count": 3,
                "comment_count": 0,
                "liked_by_user": False,
            }
        ],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.comments_for_projects",
        lambda _ids: {12: []},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.suggested_users",
        lambda _user_id: [],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [{"category_id": 1, "category_name": "Graphic Design"}],
    )

    response = client.get("/feed")

    assert response.status_code == 200
    assert b"News feed" in response.data
    assert b"A new poster design." in response.data
    assert b"Recommendations" in response.data
    assert b"dashboard.css" in response.data
    assert b"dashboard.css?v=" in response.data
    assert response.headers["Cache-Control"] == "no-store"
    assert b'id="dashboard-mobile-menu"' not in response.data
    assert b'class="dashboard-menu-button"' not in response.data
    assert b"dashboard-settings-link" in response.data
    assert b'aria-label="Settings"' in response.data
    assert b'class="mobile-add"' not in response.data
    assert b">+ Post</a>" not in response.data
    assert b"<small>Feed</small>" in response.data
    assert b"<small>Notifications</small>" in response.data
    assert b'class="mobile-nav-bell"' in response.data
    assert b"<small>Friends</small>" not in response.data
    assert b"Copy post link" in response.data
    assert b"Save post" in response.data
    assert b"Notifications" in response.data
    assert b'class="nav-notification-badge">3' in response.data


def test_suggestions_show_follow_back_and_unfollow_without_disappearing(
    client, monkeypatch
):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_feed",
        lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.comments_for_projects",
        lambda _ids: {},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.suggested_users",
        lambda _user_id: [
            {
                "user_id": 8,
                "full_name": "Already Followed",
                "username": "followed",
                "profession": None,
                "profile_image": None,
                "followed_by_viewer": True,
                "follows_viewer": False,
            },
            {
                "user_id": 9,
                "full_name": "New Follower",
                "username": "follower",
                "profession": None,
                "profile_image": None,
                "followed_by_viewer": False,
                "follows_viewer": True,
            },
        ],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [],
    )

    response = client.get("/feed")

    assert response.status_code == 200
    assert b"Already Followed" in response.data
    assert b"Unfollow" in response.data
    assert b"New Follower" in response.data
    assert b"Follow back" in response.data
    assert b'data-target-user-id="8"' in response.data
    assert b'data-follows-viewer="true"' in response.data


def test_follow_action_returns_to_current_page(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    toggled = []
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.toggle_follow",
        lambda user_id, target_id: toggled.append((user_id, target_id)) or True,
    )

    response = client.post(
        "/users/8/follow",
        data={"next": "/users/maya/followers"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/users/maya/followers")
    assert toggled == [(7, 8)]


def test_follow_ajax_updates_without_redirect(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.toggle_follow",
        lambda user_id, target_id: (user_id, target_id) == (7, 8),
    )

    response = client.post(
        "/users/8/follow",
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "following": True,
        "target_user_id": 8,
    }


def test_like_ajax_updates_without_redirect(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_visible_post",
        lambda *_args: {"project_id": 12, "user_id": 8},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.toggle_like",
        lambda *_args: True,
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.post_engagement_counts",
        lambda _project_id: {"like_count": 4, "comment_count": 2},
    )

    response = client.post(
        "/posts/12/like",
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "liked": True,
        "like_count": 4,
        "comment_count": 2,
    }


def test_comment_ajax_returns_new_comment_without_redirect(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    created = []
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_visible_post",
        lambda *_args: {"project_id": 12, "user_id": 8},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.add_comment",
        lambda user_id, project_id, text: created.append(
            (user_id, project_id, text)
        ),
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.post_engagement_counts",
        lambda _project_id: {"like_count": 4, "comment_count": 3},
    )

    response = client.post(
        "/posts/12/comments",
        data={"comment_text": "Looks excellent!"},
        headers={"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"},
    )

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()["comment"] == {
        "full_name": "Arun Rai",
        "text": "Looks excellent!",
    }
    assert response.get_json()["comment_count"] == 3
    assert created == [(7, 12, "Looks excellent!")]


def test_post_owner_sees_management_menu(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_feed",
        lambda _user_id, category_id=None: [
            {
                "project_id": 15,
                "user_id": 7,
                "title": None,
                "description": "My post",
                "cover_image": None,
                "status": "published",
                "created_at": datetime(2026, 7, 24),
                "full_name": "Arun Rai",
                "username": "arun",
                "profession": "Designer",
                "profile_image": None,
                "category_name": None,
                "like_count": 0,
                "comment_count": 0,
                "liked_by_user": False,
                "saved_by_user": False,
            }
        ],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.comments_for_projects",
        lambda _ids: {15: []},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.suggested_users",
        lambda _user_id: [],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [],
    )

    response = client.get("/feed")

    assert response.status_code == 200
    assert b"Edit post" in response.data
    assert b"Hide from public" in response.data
    assert b"Delete post" in response.data
    assert b"Save post" not in response.data


def test_category_recommendation_filters_feed(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    selected = {}

    def fake_feed(_user_id, category_id=None):
        selected["category_id"] = category_id
        return []

    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_feed",
        fake_feed,
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.comments_for_projects",
        lambda _ids: {},
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.suggested_users",
        lambda _user_id: [],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [{"category_id": 3, "category_name": "Illustration"}],
    )

    response = client.get("/feed?category=3")

    assert response.status_code == 200
    assert selected["category_id"] == 3
    assert b"Clear category filter" in response.data


def test_post_requires_text_or_photo(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [],
    )
    called = False

    def fake_publish(*_args):
        nonlocal called
        called = True

    monkeypatch.setattr(
        "app.controllers.socialController.publish_post",
        fake_publish,
    )

    response = client.post(
        "/posts/new",
        data={"content": "", "category_id": "0"},
    )

    assert response.status_code == 200
    assert b"Write something or choose a photo." in response.data
    assert b"Post preview" in response.data
    assert b"Square" in response.data
    assert b"Portrait" in response.data
    assert b"Landscape" in response.data
    assert called is False


def test_text_post_publishes_and_returns_to_feed(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [],
    )
    published = {}

    def fake_publish(user_id, content, image, category_id, aspect_ratio):
        published.update(
            user_id=user_id,
            content=content,
            image=image,
            category_id=category_id,
            aspect_ratio=aspect_ratio,
        )

    monkeypatch.setattr(
        "app.controllers.socialController.publish_post",
        fake_publish,
    )

    response = client.post(
        "/posts/new",
        data={"content": "My first post", "category_id": "0"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/feed")
    assert published == {
        "user_id": 7,
        "content": "My first post",
        "image": None,
        "category_id": 0,
        "aspect_ratio": "1:1",
    }


def test_owner_can_update_post(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    post = {
        "project_id": 15,
        "user_id": 7,
        "category_id": None,
        "title": None,
        "description": "Old text",
        "cover_image": None,
        "status": "published",
        "created_at": datetime(2026, 7, 24),
        "updated_at": datetime(2026, 7, 24),
    }
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_post_for_management",
        lambda *_args: post,
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.list_categories",
        lambda: [],
    )
    updated = {}

    def fake_update(
        user_id,
        existing_post,
        content,
        image,
        category_id,
        aspect_ratio,
    ):
        updated.update(
            user_id=user_id,
            project_id=existing_post["project_id"],
            content=content,
            image=image,
            category_id=category_id,
            aspect_ratio=aspect_ratio,
        )
        return True

    monkeypatch.setattr(
        "app.controllers.socialController.update_existing_post",
        fake_update,
    )

    response = client.post(
        "/posts/15/edit",
        data={"content": "Updated text", "category_id": "0"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/posts/15")
    assert updated["content"] == "Updated text"
    assert updated["aspect_ratio"] == "1:1"


def test_non_owner_cannot_edit_or_delete_post(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_post_for_management",
        lambda *_args: None,
    )

    assert client.get("/posts/99/edit").status_code == 404
    assert client.post("/posts/99/delete").status_code == 404


def test_owner_can_hide_post(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_post_for_management",
        lambda *_args: {"project_id": 15, "user_id": 7},
    )
    changed = {}

    def fake_visibility(project_id, user_id, status):
        changed.update(project_id=project_id, user_id=user_id, status=status)
        return True

    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.set_post_visibility",
        fake_visibility,
    )

    response = client.post(
        "/posts/15/visibility",
        data={"status": "hidden", "next": "/profile"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert changed == {"project_id": 15, "user_id": 7, "status": "hidden"}


def test_viewer_can_save_post_but_owner_cannot(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    toggled = []
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.toggle_saved_post",
        lambda user_id, project_id: toggled.append((user_id, project_id)) or True,
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_visible_post",
        lambda *_args: {"project_id": 15, "user_id": 8},
    )

    response = client.post(
        "/posts/15/save",
        data={"next": "/feed"},
    )

    assert response.status_code == 302
    assert toggled == [(7, 15)]

    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_visible_post",
        lambda *_args: {"project_id": 15, "user_id": 7},
    )
    assert client.post("/posts/15/save").status_code == 400


def test_profile_friends_messages_and_settings_render(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_profile_by_username",
        lambda _username, _viewer: {
            **active_user(),
            "created_at": datetime(2026, 1, 1),
            "post_count": 0,
            "follower_count": 2,
            "following_count": 3,
            "followed_by_viewer": False,
            "follows_viewer": False,
        },
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.posts_by_user",
        lambda *_args: [],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.friends_for_user",
        lambda _user_id: [],
    )

    profile_page = client.get("/profile")
    friends_page = client.get("/friends")
    messages_page = client.get("/messages")
    assert profile_page.status_code == 200
    assert b'href="/users/arun/followers"' in profile_page.data
    assert b'href="/users/arun/following"' in profile_page.data
    assert friends_page.status_code == 200
    assert b"Coming soon" in messages_page.data
    settings = client.get("/settings")
    assert b"Change password" in settings.data
    assert b"Appearance" in settings.data
    assert b"Light and dark mode" in settings.data
    assert b'class="theme-toggle settings-theme-toggle"' in settings.data
    assert b'aria-labelledby="logout-heading"' in settings.data
    assert b'action="/logout"' in settings.data
    asset_urls = {
        re.search(rb'href="([^"]*dashboard\.css\?v=\d+)"', page.data).group(1)
        for page in (profile_page, friends_page, messages_page, settings)
    }
    assert len(asset_urls) == 1


def test_connections_page_lists_people_and_relationship_action(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.find_profile_by_username",
        lambda *_args: {
            **active_user(),
            "post_count": 0,
            "follower_count": 1,
            "following_count": 0,
            "followed_by_viewer": False,
            "follows_viewer": False,
        },
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.followers_for_user",
        lambda *_args: [
            {
                "user_id": 8,
                "full_name": "Maya Shrestha",
                "username": "maya",
                "profession": "Illustrator",
                "profile_image": None,
                "followed_by_viewer": False,
                "follows_viewer": True,
            }
        ],
    )

    response = client.get("/users/arun/followers")

    assert response.status_code == 200
    assert b"Followers" in response.data
    assert b"Maya Shrestha" in response.data
    assert b"Follow back" in response.data


def test_notifications_render_actions_and_are_marked_read(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)
    marked = []
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.notifications_for_user",
        lambda _user_id: [
            {
                "notification_id": 1,
                "notification_type": "follow",
                "related_project_id": None,
                "is_read": False,
                "created_at": datetime(2026, 7, 24, 10, 30),
                "sender_user_id": 8,
                "sender_name": "Maya Shrestha",
                "sender_username": "maya",
                "sender_profile_image": None,
                "followed_by_viewer": False,
                "follows_viewer": True,
            },
            {
                "notification_id": 2,
                "notification_type": "like",
                "related_project_id": 12,
                "is_read": False,
                "created_at": datetime(2026, 7, 24, 9, 0),
                "sender_user_id": 9,
                "sender_name": "Kiran Rai",
                "sender_username": "kiran",
                "sender_profile_image": None,
                "followed_by_viewer": False,
                "follows_viewer": False,
            },
        ],
    )
    monkeypatch.setattr(
        "app.controllers.socialController.socialRepository.mark_notifications_read",
        lambda user_id: marked.append(user_id),
    )

    response = client.get("/notifications")

    assert response.status_code == 200
    assert b"started following you" in response.data
    assert b"Follow back" in response.data
    assert b"liked your post" in response.data
    assert b'href="/posts/12"' in response.data
    assert marked == [7]


def test_invalid_settings_show_field_errors(client, monkeypatch):
    install_user(monkeypatch)
    log_in(client)

    response = client.post(
        "/settings/profile",
        data={
            "profile-full_name": "A",
            "profile-profession": "",
            "profile-biography": "",
            "profile-website_url": "not-a-url",
        },
    )

    assert response.status_code == 200
    assert b"Field must be between 2 and 120 characters long." in response.data
    assert b"Invalid URL." in response.data
