Changelog
=========


1.0a6 (unreleased)
------------------

- Change permissions / wokflows for institutions, meetings, items & folders
  Institution Managers have now less possibilities & actions
  [laulaz]

- The watermark "in project" is also displayed when the item is still private
  [odelaere]

- Added publishable management for annexe synchronization
  [odelaere]

- Added Additional data field on items to tweak the display of some data depending of the institution config.
  [odelaere]


1.0a5 (2019-12-13)
------------------

- Improved Item View
  [odelaere]

- Improved CSS
  [thomlamb]

- Fixed date management in Sync
  [gbastien]

1.0a4 (2019-12-11)
------------------

- Use conditional formatted title for items : PMLIE-381
  [laulaz]

- Improve faceted criteria : PMLIE-381
  [laulaz]

- Added annexe file synchronization
  [odelaere]

- Added item project decision disclaimer views
  [odelaere]

- Added item_title_formatting_tal
  [odelaere]

- Added disclaimer for decision in project
  [odelaere]

- Fixed robot
  [odelaere]

- Removed refused feature : item-type
  [odelaere]

- Fix label for item_decision_formatting_tal
  [odelaere]

- Removed count on meeting date vocabulary
  [odelaere]

- Fix month was not properly translated in meeting_date vocabulary
  [odelaere]

- Removed unused import
  [odelaere]

- Renamed deliberation to decision so it's less confusing
  [odelaere]

- Update translations
  [odelaere]

- Fix tests in python 2.7
  [odelaere]

- Removed attendees from meeting
  [odelaere]

- format_meeting_date() done. Using it in MeetingDateVocabularyFactory. (#1)
  [duchenean]

- roll back
  [odelaere]

- re enable current selected filter view
  [odelaere]

- Use @search_items instead @search_meeting_items
  [gbastien]

- Avoid an error with dict comparison on Python 3.7
  [mpeeters]

- Fix item deliberation format
  [odelaere]


1.0a3 (2019-11-28)
------------------

- Update french translations
  [mpeeters]

- Added feature : force resync a meeting
  [odelaere]

- factorize sync methods
  [odelaere]

- Drop Plone 5.1 and 5.0 support
  [mpeeters]

- Managed info_points_formatting_tal in sync
  [odelaere]

- Manage last modification date sync format for meeting
  [jjaumotte]

- Add `collective.fingerpointing` to the package dependencies
  [mpeeters]

- Add tests for utils functions
  [mpeeters]

- Publish demo profile content
  [mpeeters]

- Add tests for faceted criteria
  [mpeeters]

- Add tests for utils, item and institution views
  [mpeeters]

- Add `plonemeeting_last_modified` for demo data
  [mpeeters]

- Fix attendees unicode
  [boulch]

- Add sync Tests
  [boulch]

- Fix update of meeting items during sync
  [mpeeters]

- Add a validator for meeting and meeting item import additional parameters
  [mpeeters]

- Fix robot tests
  [mpeeters]

- Redirect on faceted view after importing a meeting
  [mpeeters]

- They may be 0 or 1 or more Representatives in charge of an item
  [odelaere]

- Use additional query strings in API requests
  [laulaz]

- Add basic sync for meeting items & fix localized date conversion
  [laulaz]

- Added plonemeeting_last_modified to keep track of sync status more easily
  [odelaere]

- Restrict import action to institutions
  [laulaz]

- set and format attendees (assembly, assembly excused, assembly absents)
  [duchenean, boulch]


1.0a2 (2019-11-25)
------------------

- Fix import meeting form
  [laulaz]

- Fix institution view
  [laulaz]

- Don't use plone.directives anymore (deprecated)
  [laulaz]


1.0a1 (2019-11-25)
------------------

- Initial release.
  [laulaz]
