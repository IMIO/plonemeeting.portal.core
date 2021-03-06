Changelog
=========


1.1.1 (unreleased)
------------------

- Nothing changed yet.


1.1.0 (2020-10-27)
------------------

- Refactored LESS theme to be more mobile-friendly.
  [aduchene]
- Updated iA.Delib API calls using @search method
  [odelaere]

1.0.9 (2020-09-22)
------------------

- Hide representatives_in_charge on faceted view if it's not used.
  [aduchene]
- Fixed ValueError: Circular reference detected on Item/folder_contents view
  by adding an indexer on formatted_title Item field.
  [aduchene]


1.0.8 (2020-09-11)
------------------

- Added properties on institution to choose navigation bar colors.
  [aduchene]
- Grouped styling properties on institution under "Styling" tab.
  [aduchene]
- Added a dynamic css generation view ('@@custom_colors.css')
  to generate a custom css with institutions colors
  [aduchene]
- Added one event handler for institution, so it call the 'custom_colors.css' view to recompile
  the css on institution change (added and modified events) and then store it in the registry
  [aduchene]
- Refactored CSS theme to LESS to ease maintenance, readability and futur developments.
  [aduchene]
- Theme can now be recompiled TTW with the resourceregistry-controlpanel.
  [aduchene]
- Changed the default loading animation of eea.facetednavigation to use one more neutral.
  [aduchene]
- Tweaked the theme : faceted widget are now correctly aligned on desktop (no useless margin-left),
  first item-preview didn't need a margin-top on decisions page, rounded corners on meeting-info,...
  [aduchene]


1.0.7.3 (2020-07-15)
--------------------

- updated source of upgrade step.
  [odelaere]


1.0.7.2 (2020-07-15)
--------------------

- Upgrade libs for debugging tools.
  [odelaere]


1.0.7.1 (2020-07-13)
--------------------

- Added sortable number on Item.
  [odelaere]


1.0.6 (2020-06-08)
------------------

- Update dependencies. Use eea.facetednavigation >= 13.8 to fix pagination with restapi.
  [odelaere]


1.0.5 (2020-01-28)
------------------

- Do not break faceted view when no meeting to display.
  [gbastien]
- Added parameter force=False to sync.sync_annexes_data so when forcing
  reimport, the annexes are reimported as well.
  [gbastien]
- Take into account the institution.info_annex_formatting_tal while importing
  annexes, by default annex title is the original annex title.
  [gbastien]


1.0.4 (2020-01-24)
------------------

- Fixed display of empty meetings.
  [odelaere]


1.0.3 (2020-01-23)
------------------

- Require collective.cookiecuttr > 1.0 (Python3 compat).
  [gbastien]
- Manager is able to edit field IMeeting.date_time, this is useful to add
  old meetings not managed by the synchronization.
  [gbastien]
- Fix sync : object could not be deleted by institution manager
  [odelaere]


1.0.2 (2020-01-17)
------------------

- Fixed styles.


1.0.1 (2020-01-17)
------------------

- Colorize entire footer links, not only #portal-anontools.
  [gbastien]


1.0 (2020-01-17)
----------------

- Allow reorder mapping fields of an institution.
  [odelaere]

- Force reload button should be red.
  [odelaere]

- Added disclaimer in footer (using CMS Plone and made with IMIO).
  [gbastien]


1.0rc10 (2020-01-16)
--------------------

- Fixed portal logo


1.0rc9 (2020-01-16)
-------------------

- Improved UX


1.0rc8 (2020-01-15)
-------------------

- Improved disclaimer on item preview
  [odelaere]


1.0rc7 (2020-01-15)
-------------------

- Customize footer to add Log In link in portal.footer
  This is impossible with viewlet moving (because of Barceloneta rules)
  [laulaz]

- Added subscriber to delete institution manager group when an institution is deleted
  [odelaere]

- Allow Institution Managers to add content
  [laulaz]

- Add alt's on actions
  [laulaz]

- Fix display of formatted title in item preview.
  [odelaere]

- Added force reload on meeting preview.
  [odelaere]


1.0rc6 (2020-01-10)
-------------------

- CSS: remove underline when hovering meeting date on item view
  [gbastien]

- Faceted ItemsSortWidget, do only use double sorting
  ('linkedMeetingDate', 'item_number') when not meeting (criterion 'seance')
  is selected in the faceted.  This should fix the weird results on last page
  of items of a meeting
  [gbastien]

- Renamed 'Publish' french translation to 'Mettre en décision'
  [gbastien]

1.0rc5 (2020-01-10)
-------------------

- Store storable value in index 'item_number', turn str item number
  into a sortable integer
  [gbastien]

- Added 'sort_on=getItemNumber' to default URL returned
  by utils.get_api_url_for_meeting_items
  [gbastien]

- Set 'b_size=9999' for restapi URi returned by
  utils.get_api_url_for_meeting_items and utils.get_api_url_for_meetings
  [gbastien]

- Use default Plone CSS classes to manage review_state
  [gbastien]

- Create role 'Institution Manager'
  [gbastien]

1.0rc4 (2020-01-09)
-------------------

- Fixed Flake8 config.
  [odelaere]

1.0rc3 (2020-01-09)
-------------------

- Updated status colors.
  [thomlamb]

1.0rc2 (2020-01-08)
-------------------

- Fixed check for meeting actions, permission is
  'Modify portal content', not 'Modify Portal Content'
  [gbastien]

1.0rc1 (2020-01-08)
-------------------

- Various fixes on the UX

1.0b1 (2020-01-07)
------------------

- Add eye icon to redirct to meeting view
  [odelaere]

- Finalized annexes sync
  [odelaere]

- Add pencil & sync icons to manage meeting
  [laulaz]

- Move login viewlet to footer
  [laulaz]

- Add show / hide toggle on meeting custom info
  [laulaz]

- Add annexes on faceted, and handle icons
  [laulaz]

- Allow inline 'style' attribute
  [laulaz]

- Change permissions / wokflows for institutions, meetings, items & folders
  Institution Managers have now less possibilities & actions
  [laulaz]

- The watermark "in project" is also displayed when the item is still private
  [odelaere]

- Added publishable management for annexe synchronization
  [odelaere]

- Added Additional data field on items to tweak the display of some data depending of the institution config.
  [odelaere]

- While importing an item, if `groupsInCharge` is empty, use the
  `all_groupsInCharge` data on item that contains groupsInCharge
  defined on ithe item proposingGroup or category.
  [gbastien]

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
