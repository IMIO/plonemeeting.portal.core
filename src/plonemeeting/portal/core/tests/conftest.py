from pytest_plone import fixtures_factory
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING
from plonemeeting.portal.core.testing import PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING
pytest_plugins = ["pytest_plone"]


globals().update(
    fixtures_factory(
        (
            (PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING, "acceptance"),
            (PLONEMEETING_PORTAL_DEMO_FUNCTIONAL_TESTING, "functional"),
            (PLONEMEETING_PORTAL_CORE_INTEGRATION_TESTING, "integration"),
        )
    )
)
