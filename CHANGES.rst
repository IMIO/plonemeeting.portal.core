Changelog
=========

2.2.1 (2025-09-10)
------------------

- Integrate collective.documentgenerator to generate a documents from content types.
  [aduchene]
- Add default templates for `Publication` to be used by collective.documentgenerator.
  [aduchene]
- Add missing plone.icons to content types.
  [aduchene]

2.2.0 (2025-09-08)
------------------

- DELIBE-251: New timestamping format (ASiC) for publications, combining the archive and the timestamp in a single file.
  [aduchene]
- DELIBE-228: Add a new JS form to validate the new publication timestamping format.
  [aduchene]
- Adapt `publication.pt` to include new timestamping format.
  [aduchene]

2.1.12 (2025-07-01)
-------------------

- DELIBE-245: timestamp invalidation overhaul.
  [aduchene]
- Change the map center offset to be more centered on the institution.
  [aduchene]
- Make the PDF Viewer displaying pages in full width by default.
  [aduchene]
- Remove the the `get_resource` patch.
  [aduchene]
- DELIBE-249: Allow to directly publish a publication in private state with an effective date.
  [aduchene]

2.1.11 (2025-06-19)
-------------------

- Fix an issue with `publication.EditForm`.
  [aduchene]

2.1.10 (2025-06-19)
-------------------

- Prevent Editor to edit a publication in planned state.
  [aduchene]
- Move table_of_contents field to the general fieldset.
  [aduchene]
- Prevent and show an error message when a publication effective date is removed in planned state.
  [aduchene]
- Add missing translations.
  [aduchene]

2.1.9 (2025-06-12)
------------------

- Fix bad release.
  [aduchene]

2.1.8 (2025-06-12)
------------------

- Fix wrong permission in `preview_meeting.pt`.
  [aduchene]
- DELIBE-111: Add a warning message to the publication manager if the publication date is in the past.
  [aduchene]
- DELIBE-206: Add `webstats_js` field on Institution and override AnalyticsViewlet to use it.
  [aduchene]
- DELIBE-237: Fix no effective date when timestamping was disabled.
  [aduchene]

2.1.7 (2025-05-19)
------------------

- DELIBE-224: Fix file upload issue in the rich text editot's content browser.
  [aduchene]

2.1.6 (2025-05-14)
------------------

- DELIBE-221: Fix an permission issue with the "Add meeting" button in the faceted view.
  [aduchene]
- DELIBE-223: Fix bleeding groups from other institutions in manage-edit-user view.
  [aduchene]
- Add a back button to the File view.
  [aduchene]
- Refactor and extract annexes into macros.
  [aduchene]

2.1.5 (2025-05-12)
------------------

- DELIBE-222: Fix an issue regarding the last Contentbrowser changes.
  [aduchene]

2.1.4 (2025-05-06)
------------------

- Change default timestamping service in default profile.
  [aduchene]
- Make sure Contentbrowser is using the navigation root as rootPath.
  [aduchene]

2.1.2 (2025-04-30)
------------------

- DELIBE-199: Users are now manageable by institution.
  [aduchene]
- DELIBE-199: Add new member and manager groups for each institution.
  [aduchene]
- DELIBE-199: New institution settings navigation tab and view.
  [aduchene]

2.1.1 (2025-03-21)
------------------

- DELIBE-23/DELIBE-206: Complete the upgrade step 2100.
  [aduchene]
- DELIBE-24: Fix an issue where a decisions manager could not remove items from a meeting.
  [aduchene]
- Handle multiple possible cron paths in the Prometheus export view.
  [aduchene]

2.1.0 (2025-02-28)
------------------

- DELIBE-196: Plone 6.1 compatibility.
  [aduchene]
- DELIBE-23/DELIBE-206: Uninstall collective.cookiecuttr.
  [aduchene]

2.0.6 (unreleased)
------------------

- DELIBE-186: Add a new Prometheus export view `prometheus-export` to monitor cron.
  [aduchene]
- Complete tests about `MeetingAgendaAPIView`.
  [aduchene]
- Rename `institution_locations` view name to `institution-locations`.
  [aduchene]

2.0.5 (2024-12-19)
------------------

- DELIBE-12: Avoid a "@@confirm-action" on `Institution` creation.
  [aduchene]
- DELIBE-29: Add ZoomControl back on institutions map
  [aduchene]
- DELIBE-180: Fix some issues when an `Institution.representatives_mappings` could be None.
  [aduchene]

2.0.4 (2024-10-23)
------------------

- DELIB-11: Fixed an issue with next/prev navigation on `ItemView` when items are not in correct order
  in the meeting folder.
  [aduchene]
- DELIBE-3: Add meeting date in the title of `PreSyncForm` and `PreImportForm`.
  [aduchene]

2.0.3 (2024-10-10)
------------------

- Removed ipdb.
  [aduchene]

2.0.2 (2024-10-08)
------------------

- Fixed call to `@@update_meeting` and `@@force_reimport_meeting` that was broken
  because we were passing the `decisions` folder instead the `Institution`.
  [gbastien]
- Fixed issue in pre-sync form when an item is removed and classifier field is used.
  [aduchene]
- Fixed issue with anonymous that could not download the timestamp field on `Publication`.
  [aduchene]

2.0.1 (2024-10-02)
------------------

- Fixed wrong link on `preview_meeting.pt`.
  [aduchene]
- Adapted `meeting_workflow` so `Editor` may change a meeting `review_state`
  and not only the `Owner`.  `Owner` is not more managed by `meeting_workflow`.
  Fix meeting `review_state` could not be changed by another user than the `Owner`.
  [gbastien]
- Fixed publication effective date not reindexed after publish.
- Splitted `avis` `document_type` in 3 `document_types`
  (`avis`, `avis-enquete-publique` and `avis-reunion-information`),
  `avis` `id` kept for backward compatibility for publications already created.

2.0.0 (2024-09-23)
------------------

- Fixed project disclaimer message displayed on item in `decision`,
  display it only when item is not in `decision`.
  [gbastien]
- Fixed wrong `meeting_type` on `preview_meeting.pt`.
  [aduchene]

2.0.0b1 (2024-09-17)
--------------------

- Plone 6 compatibility.
  [aduchene]
- Theme extracted to `plonetheme.deliberations` package.
  [aduchene]
- Use latest Python 3.12 and Plone 6.0.13.
  [aduchene]
- "Publications" feature :

  - Rename "meetings" folder to "decisions".
  - Use `collective.autopublishing` to manage automatic publishing of publications.
  - Use `collective.timestamp` to manage publication timestamping.
  - Use `imio.webspellchecker` to have better webspellchecking.
  - Add `Publication` content type.
  - Add `Publication` views and faceted navigation.
  - Add custom workflows to manage publications and folders.
  - Add new groups `*-publications-manager` for each institution to manage publications.
  - Add some unit tests about the feature.
  - Add an upgrade step to migrate meetings and items in decisions folder.
  - Miscellaneous fixes and tweaks to make it work nicely.

  [gbastien, laulaz, aduchene]

1.6.3 (2024-02-19)
------------------

- Added `general-assembly` to the registry `meeting_types`.
  [gbastien]
- Upgrade dependencies versions.
  [aduchene]

1.6.2 (2023-09-18)
------------------

- Added "Province" and "Séance publique du Conseil Provincial" to institution type and meeting type.
  [aduchene]
- Added hcaptcha to contact-info form
  [aduchene]
- Fixed wrong action link on meeting_preview.pt
  [aduchene]

1.6.1 (2022-12-08)
------------------

- Fixed an issue with default ordering column on pre import form.
  [aduchene]


1.6.0 (2022-12-08)
------------------

- Added `Annexes?` faceted filter only displayed to institution manager,
  this rely on new portal_catalog index `has_annexes`.
  Upgrade step to 1009 needs to be run.
  [gbastien]
- Be coherent with institutions created at the beginning with the id of the folder
  holding faceted filters in the institution, use id `seances` instead `meetings`.
  [gbastien]
- install_requires: imio.helpers>=0.65.
  [aduchene]
- Add a pre import form and a pre sync form before importing/synchronizing a meeting #PM-3291.
  [aduchene]


1.5.1 (2022-07-25)
------------------

- Use plone 5.2.9.
  [odelaere]
- Handle deactivated representatives.
  [odelaere]


1.5.0 (2022-06-17)
------------------

- Properly redirect anonymous users when using meeting direct url.
  [odelaere]
- Added item number handling in sync process.
  [odelaere]
- Reworked sync + allow partial sync of arbitrary items.
  [odelaere]
- Auto cancel ImportMeetingForm if failed to connect to iA.Delib.
  [odelaere]
- Fix bad status code would raise an unexpected error #PM-3805.
  [odelaere]
- Fix history is lost in some case after resync representatives from delib #PM-3816.
  [odelaere]
- Moved upgrade steps in a separate `migrations` module and changed configure.zcml accordingly.
  [aduchene]
- Added an utils function `get_term_title` to easily get the term title of a given context and fieldname.
  [aduchene]
- Added two new fields `institution_type` and `meeting_type` on Institution.
  Added an upgrade step to 1008 to add the vocabulary values in the registry.
  [aduchene]
- Reworked homepage_view according to the new field `institution_type`.
  InstitutionSelect component is now properly decomposed in sub-components.
  [aduchene]
- Reworked faceted view according to the new field `meeting_type`.
  [aduchene]
- Updated theme and frontend dependencies.
  [aduchene]
- Use HTTPS protocol for mr.developer.
  [aduchene]
- Added a cross-checking against publishable annexes, to be sure it can be published.
  [aduchene]
- Fixed import meeting form as pre-report sync is not already merged.
  [aduchene]
- Require `imio.helpers>=0.58` so we get the fix in `xhtml.replace_content` that
  makes sure anonymized text is correctly handled (was failing when containing sub tags).
  [gbastien]

1.4.5 (2021-11-29)
------------------

- Update to eea.facetednavigation 14.7.
  [odelaere]


1.4.4 (2021-09-30)
------------------

- Update default rgpd_masked_text_redirect_path because anchor doesn't work as expected.
  [odelaere]


1.4.3 (2021-09-29)
------------------

- Added output filter for anonymized content.
  [odelaere]


1.4.2 (2021-09-28)
------------------

- Fix invariant while adding new Institution.
  [odelaere]


1.4.1 (2021-09-23)
------------------

- Don't show unpublished faq on homepage.
  [aduchene]
- Highlight region on Leaflet map.
  [aduchene]
- Use JsonMinimizerPlugin to minimize .json file
  [aduchene]


1.4.0 (2021-09-21)
------------------

- Upgraded datagridfield version.
  [odelaere]
- Fail institution edit form validation if an iA.Delib category is mapped multiple times.
  [odelaere]
- Handle connection failure properly in institution edit form.
  [odelaere]
- Amper removing of representatives if they are linked to at least an item.
  [odelaere]
- Removed faceted-preview-meeting-items.
  [odelaere]
- Added DataGridField to manage url parameters.
  [odelaere]
- Query representatives from iA.Delib to populate vocabularies only when loading the edit form.
  [odelaere]
- Fetched representatives from delib are kept if used.
  [odelaere]
- Changed build system for frontend development (plone-compile-resources => webpack 5).
  [aduchene]
- Added a new view for Plone site root (new homepage).
  [aduchene]
- Added some assets and JS resources to the bundle (new homepage).
  [aduchene]


1.3.3.2 (2021-08-20)
--------------------

- Do not fail to edit `Institution` if service to fetch categories is broken.
  [gbastien]
- Adapted `SelectMeetingWidget` used for the `seances` criterion to make
  zero count values shown and selectable.
  [gbastien]


1.3.3.1 (2021-08-16)
--------------------

- Query categories from iA.Delib to populate vocabularies only when loading the edit form.
  [odelaere]
- Added automatic initialization of categories mapping.
  [odelaere]
- Fixed applying the demo profile at new Plone Site creation time.
  This was due to BrowserLayers still not initialized, in this case we mark the
  `REQUEST` with registred `BrowserLayers` ourselves.
  [gbastien]
- Added default value for `Institution.meeting_config_id`
  [odelaere]
- Adapted code to receive the smallest JSON possible by using
  include parameters in the json query.
  [gbastien]
- Rename actions available on meeting.
  [odelaere]
- Improved translations in Institution edit form.
  [odelaere]


1.3.3 (2021-06-28)
------------------

- Fixed long representative value ws not used.
  [odelaere]
- Fixed error while compiling rules.xml by institution manager.
  [gbastien]
- Fix type constraints on Folder content type and faceted folders.
  [odelaere]
- Merged faceted folders in `Institution` , `meetings` and `decisions` were
  merged and only `meetings` folder is kept, new faceted behavior
  is a mix of old behaviors.
  [gbastien]


1.3.2 (2021-06-15)
------------------

- Updated LESS to manage images width/height correctly on mobile.
  [gbastien]
- Filter imported items based on mapped categories or VOID if no mapping #PM-3436.
  [odelaere]
- Ignore not mapped representatives_in_charge.
  [aduchene]
- Filter imported items based on mapped representatives if a mapping exists #PM-3437.
  [odelaere]
- Updated LESS and JS to add an environment label when necessary.
  [aduchene]
- Updated theme : fixed meeting-metadata on Item view to be more readable
  [aduchene]
- Fixed formatted_title not set when syncing.
  [aduchene]
- Use `imio.helpers.content.richtextval` to set a `RichTextValue`.
  [aduchene]
- Keep representative order defined on item in item preview.
  [odelaere]
- Install `plone.restapi` but give the `UseRESTAPI` permission to role `Member`
  instead `Anonymous` by default.
  [gbastien]
- Fix institution automatic transition fails on Meeting # PM-3441.
  [odelaere]
- Now that we use `text/x-html-safe` as `outputMimeType` for stored
  `RichTextValue` for item `decision` field, needed to monkey patch
  `Products.PortalTransforms.safe_html.hasScript` function to accept
  `data:image` base64 value.
  [gbastien]



1.3.1 (2021-04-29)
------------------

- Fixed locale issues.
  [aduchene]
- Updated LESS theme to add more padding around faceted view.
  [aduchene]


1.3 (2021-04-27)
----------------

- Fix open annexe files in new tab.
  [odelaere]
- Fix Institution icon minimum size when uploading svg.
  [odelaere]
- Fix custom CSS colors not updating when an institution was not published.
  [aduchene]
- Revamped Intitution views using default plone.dexterity template.
  [odelaere].
- Allow using classifier field from json instead of category.
  [odelaere]
- Transition events on Institution Folder also apply on its children.
  [odelaere]
- Only managers can add folders.
  [odelaere]


1.2 (2021-03-24)
----------------

- Do not break when importing an annex if annex `filename` is `None`.
  [gbastien]
- When calling the `annexes endpoint` to get annexes for an item, call it with
  `?publishable=true` so only publishable annexes are serialized and returned by
  PloneMeeting which speed things a lot.
  We do no more manage the case when `publishable_activated=false`, we consider
  that `publishable` is always activated.
- Adapted code to be compatible with version `4.1.x` and `4.2.x`
  of `Products.PloneMeeting`.
  [gbastien]


1.1.1 (2021-02-25)
------------------

- Hidden faceted and ical actions.
  [odelaere]


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
