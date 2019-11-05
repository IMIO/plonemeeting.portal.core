# ============================================================================
# DEXTERITY ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s plonemeeting.portal.core -t test_item.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src plonemeeting.portal.core.testing.PLONEMEETING_PORTAL_CORE_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot /src/plonemeeting/portal/core/tests/robot/test_item.robot
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

Scenario: As a site administrator I can add a Item
  Given a logged-in site administrator
    and an add Meeting form
   When I type 'My Item' into the title field
    and I submit the form
   Then a Item with the title 'My Item' has been created

Scenario: As a site administrator I can view a Item
  Given a logged-in site administrator
    and a Item 'My Item'
   When I go to the Item view
   Then I can see the Item title 'My Item'


*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site administrator
  Enable autologin as  Site Administrator

an add Meeting form
  Go To  ${PLONE_URL}/++add++Meeting

a Item 'My Item'
  Create content  type=Meeting  id=my-item  title=My Item

# --- WHEN -------------------------------------------------------------------

I type '${title}' into the title field
  Input Text  name=form.widgets.IBasic.title  ${title}

I submit the form
  Click Button  Save

I go to the Item view
  Go To  ${PLONE_URL}/my-item
  Wait until page contains  Site Map


# --- THEN -------------------------------------------------------------------

a Item with the title '${title}' has been created
  Wait until page contains  Site Map
  Page should contain  ${title}
  Page should contain  Item created

I can see the Item title '${title}'
  Wait until page contains  Site Map
  Page should contain  ${title}
