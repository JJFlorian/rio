import typing as t

import pytest

import rio.app_server


class FakeComponent(rio.Component):
    pass


class FakeSession:
    def __init__(self) -> None:
        self._base_url = rio.URL("http://unit.test/foo")


@pytest.mark.parametrize(
    "relative_url, expected_result",
    [
        ("", "http://unit.test/foo/bar/hello"),
        ("page-1", "http://unit.test/foo/bar/page-1"),
        ("../page-1", "http://unit.test/foo/page-1"),
        ("/page-1", "http://unit.test/foo/page-1"),
        ("http://unit.test", "http://unit.test"),
        ("https://some.where/else", "https://some.where/else"),
    ],
)
def test_make_url_absolute(relative_url: str, expected_result: str) -> None:
    session = t.cast(rio.Session, FakeSession())
    session._base_url = rio.URL("http://unit.test/foo")
    session._active_page_url = rio.URL("http://unit.test/foo/bar/hello")

    result = rio.Session._make_url_absolute(session, relative_url)
    assert str(result) == expected_result


PAGES = [
    rio.ComponentPage(
        name="Home",
        url_segment="",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Page 1",
        url_segment="page-1",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Page 2",
        url_segment="page-2",
        build=FakeComponent,
    ),
    rio.ComponentPage(
        name="Guard to Page 1",
        url_segment="guard-to-page-1",
        build=FakeComponent,
        guard=lambda _: "page-1",
    ),
    rio.ComponentPage(
        name="Guard to Cycle 1",
        url_segment="guard-to-cycle-1",
        build=FakeComponent,
        guard=lambda _: "guard-to-cycle-2",
    ),
    rio.ComponentPage(
        name="Guard to Cycle 2",
        url_segment="guard-to-cycle-2",
        build=FakeComponent,
        guard=lambda _: "guard-to-cycle-1",
    ),
    rio.Redirect(
        url_segment="redirect-to-page-1",
        target="page-1",
    ),
    rio.Redirect(
        url_segment="redirect-to-cycle-1",
        target="guard-to-cycle-2",
    ),
    rio.Redirect(
        url_segment="redirect-to-cycle-2",
        target="guard-to-cycle-1",
    ),
]


@pytest.mark.parametrize(
    "relative_url_before_redirects, relative_url_after_redirects_should",
    [
        # No redirects
        (
            "/page-1",
            "/page-1",
        ),
        (
            "/page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/page-1#foo",
            "/page-1#foo",
        ),
        # "Wrong" casing
        (
            "/Page-1",
            "/Page-1",
        ),
        # Redirects by guard
        (
            "/guard-to-page-1",
            "/page-1",
        ),
        (
            "/guard-to-page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/guard-to-page-1#foo",
            "/page-1#foo",
        ),
        # Redirects by `rio.Redirect`
        (
            "/redirect-to-page-1",
            "/page-1",
        ),
        (
            "/redirect-to-page-1?foo=bar",
            "/page-1?foo=bar",
        ),
        (
            "/redirect-to-page-1#foo",
            "/page-1#foo",
        ),
        # No such page
        (
            "/non-existent-page",
            "/non-existent-page",
        ),
        (
            "/non-existent-page?foo=bar",
            "/non-existent-page?foo=bar",
        ),
        (
            "/non-existent-page#foo",
            "/non-existent-page#foo",
        ),
        # TODO: Add tests for URLs with Unicode characters & escaped/unescaped
        # URLs
    ],
)
def test_redirects(
    relative_url_before_redirects: str,
    relative_url_after_redirects_should: str,
) -> None:
    """
    Simulate navigation to URLs, run any guards, and make sure the final,
    resulting URL is correct.
    """
    # Create a fake session. It contains everything used by the routing system.
    app = rio.App(pages=PAGES)
    app_server = rio.app_server.TestingServer(app)
    session = app_server.create_dummy_session()

    # Determine the final URL
    active_pages_and_path_arguments, absolute_url_after_redirects_is = (
        rio.routing.check_page_guards(
            session,
            session._base_url.join(rio.URL(relative_url_before_redirects)),
        )
    )

    # Verify the final URL
    absolute_url_after_redirects_should = session._base_url.join(
        rio.URL(relative_url_after_redirects_should)
    )

    assert (
        absolute_url_after_redirects_is == absolute_url_after_redirects_should
    )


def test_url_parameter_parsing_failure() -> None:
    def build_int_page(path_param: int):
        return rio.Text(str(path_param))

    int_page = rio.ComponentPage(
        name="Int Page",
        url_segment="{path_param}",
        build=build_int_page,
    )

    def build_float_page(path_param: float):
        return rio.Text(str(path_param))

    float_page = rio.ComponentPage(
        name="Float Page",
        url_segment="{path_param}",
        build=build_float_page,
    )

    app = rio.App(pages=(int_page, float_page))
    app_server = rio.app_server.TestingServer(app)
    session = app_server.create_dummy_session()

    active_pages_and_path_arguments, _ = rio.routing.check_page_guards(
        session,
        session._base_url.join(rio.URL("/3.5")),
    )

    assert active_pages_and_path_arguments is not None
    assert len(active_pages_and_path_arguments) == 1
    assert active_pages_and_path_arguments[0][0] == float_page
    assert active_pages_and_path_arguments[0][1] == {"path_param": 3.5}


def test_redirect_offsite() -> None:
    """
    Redirect to a site other than this app.
    """
    page = rio.ComponentPage(
        name="Home",
        url_segment="",
        build=FakeComponent,
    )

    app = rio.App(pages=(page,))
    app_server = rio.app_server.TestingServer(app)
    session = app_server.create_dummy_session()

    external_url = rio.URL("http://example.com")

    active_pages_and_path_arguments, absolute_url_after_redirects = (
        rio.routing.check_page_guards(
            session,
            external_url,
        )
    )

    assert active_pages_and_path_arguments is None
    assert absolute_url_after_redirects == external_url
