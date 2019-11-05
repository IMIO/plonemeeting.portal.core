# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s plonemeeting.portal.core -t test_annex.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src plonemeeting.portal.core.testing.PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/plonemeeting/portal/core/tests/robot/test_annex.robot
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

Scenario: As a site administrator I can add a Annex
  Given a logged-in site administrator
    and an add Item form
   When I type 'My Annex' into the title field
    and I submit the form
   Then a Annex with the title 'My Annex' has been created

Scenario: As a site administrator I can view a Annex
  Given a logged-in site administrator
    and a Annex 'My Annex'
   When I go to the Annex view
   Then I can see the Annex title 'My Annex'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add Item form
  Go To  ${PLONE_URL}/++add++Item

a Annex 'My Annex'
  Create content  type=Item  id=my-annex  title=My Annex

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the Annex view
  Go To  ${PLONE_URL}/my-annex
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a Annex with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the Annex title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
