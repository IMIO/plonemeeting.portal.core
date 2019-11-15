# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s plonemeeting.portal.core -t test_institution.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src plonemeeting.portal.core.testing.PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/plonemeeting/portal/core/tests/robot/test_institution.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a manager I can add a Institution
  Given a logged-in manager
    and an add Institution form
   When I type 'My Institution' into the title field
    and I submit the form
   Then a Institution with the title 'My Institution' has been created


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in Manager
  Enable autologin as  Manager

an add Institution form
  Go To  ${PLONE_URL}/++add++Institution

a Institution 'My Institution'
  Create content  type=Institution  id=my-institution  title=My Institution

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the Institution view
  Go To  ${PLONE_URL}/my-institution
  Wait until page contains  My Institution


# --- THEN -------------------------------------------------------------------

a Institution with the title '${title}' has been created
  Wait until page contains  Item created
  Page should contain  ${title}
  Page should contain  Item created

I can see the Institution title '${title}'
  Page should contain  ${title}
