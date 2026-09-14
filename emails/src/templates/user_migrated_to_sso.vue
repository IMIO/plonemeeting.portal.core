<script setup>
/**
 * "Your account now uses Wallonie Connect" ; sent once per account, by
 * `plonemeeting.portal.core.notifications.notify_user_migrated_to_sso`, when a
 * local délibérations.be account has been migrated onto its SSO identity.
 *
 * Context it expects, all of it from `notify_user_migrated_to_sso`:
 *   institution  ; the institution's title, e.g. "Ville de Namur"
 *   email        ; the address the account is now reached by, and its new userid
 *   username     ; the local username that has just stopped working
 *   login_url    ; starts the OIDC flow and comes back to the institution
 *   account_url  ; the Wallonie Connect account console ; may be EMPTY, and the
 *                  password callout drops its link when it is
 *
 * Every msgid below belongs to `plonemeeting.portal.core`, so each element that
 * carries one also carries `i18n:domain`. The shell declares `imio.emailkit` on
 * `<html>` and a nested `i18n:translate` inherits it, which would look up our
 * msgid in the kit's catalog, miss, and render the English default in every
 * language. The subject and the preheader are msgids too, but they live in
 * `emails.zcml` with the registration.
 *
 * The reader is being told about a change they did not ask for and cannot undo,
 * so the mail answers the three questions they will actually have, in order:
 * what do I type now (the card), how do I get in (the button), and what happened
 * to my password (the callout). Nothing else.
 */
</script>

<template>
  <KitMain>
    <template #pill>
      <KitPill tone="success">
        <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_pill_account_migrated" tal:omit-tag="">Account migrated</span>
      </KitPill>
    </template>

    <template #title>
      <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_title_sso_migrated" tal:omit-tag="">Your account now uses Wallonie Connect</span>
    </template>
    <template #subtitle>${institution}</template>

    <p
      i18n:domain="plonemeeting.portal.core"
      i18n:translate="email_sso_migrated_lead"
      class="m-0 text-[15px] leading-6 text-imio-grey-dark"
    >
      Your access to
      <span i18n:name="institution" tal:omit-tag="" tal:content="institution">the institution</span>
      on Délibérations.be is now managed by Wallonie Connect, the single sign-on
      service of the Walloon local authorities. Nothing you published changes; only
      the way you log in does.
    </p>

    <KitCard>
      <template #overline>
        <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_card_your_account" tal:omit-tag="">Your account</span>
      </template>
      <template #title>${email}</template>
      <KitDataList>
        <KitDataRow>
          <template #label>
            <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_field_institution" tal:omit-tag="">Institution</span>
          </template>
          ${institution}
        </KitDataRow>
        <KitDataRow>
          <template #label>
            <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_field_former_username" tal:omit-tag="">Former username</span>
          </template>
          ${username}
        </KitDataRow>
      </KitDataList>
    </KitCard>

    <!--
      The mark, then the button that repeats it in words. `portal_url` is empty
      whenever the render had no request to build an absolute URL from (a
      preview, a unit test), and a relative image url in an inbox is a
      broken-image icon, so the whole row goes rather than the src.

      A raster logo, and a white plate baked into it: mail clients do not render
      SVG, and the délibérations.be copy of this mark is white-on-magenta, which
      would vanish into the content well. Blocked images cost nothing here ; the
      `alt` and the button below say the same thing.
    -->
    <table role="presentation" tal:condition="portal_url" class="w-full">
      <tr>
        <td align="center" class="pt-2 text-[0px] leading-[0]">
          <img
            src="${portal_url}/++resource++plonemeeting.portal.core/assets/logo-wallonie-connect-mail.png"
            alt="Wallonie Connect"
            width="200"
            height="48"
            class="block"
          >
        </td>
      </tr>
    </table>

    <KitButton href="${login_url}" align="center">
      <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_cta_sso_migrated" tal:omit-tag="">Log in with Wallonie Connect</span>
    </KitButton>

    <KitPanel>
      <template #overline>
        <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_callout_password" tal:omit-tag="">Your password</span>
      </template>
      <p
        i18n:domain="plonemeeting.portal.core"
        i18n:translate="email_sso_migrated_password"
        class="m-0 text-sm leading-[22px] text-imio-black"
      >
        Your former username
        <span i18n:name="username" tal:omit-tag="" tal:content="username">username</span>
        and its password no longer work. Your password is now the one on your
        Wallonie Connect account, and that is where you change it.
      </p>
      <p tal:condition="account_url | nothing" class="m-0 pt-2 text-sm leading-[22px]">
        <a href="${account_url}" class="text-imio-magenta-dark underline" data-dark="accent"
          ><span i18n:domain="plonemeeting.portal.core" i18n:translate="email_sso_migrated_account_link" tal:omit-tag="">Manage my Wallonie Connect account</span></a>
      </p>
    </KitPanel>

    <template #mentions>
      <!--
        The address as a real link rather than plain grey text: a client that
        autolinks it styles it its own way, and one that does not leaves the
        reader retyping it by hand. `data-dark="accent"` moves it off #b3004b,
        which is around 2:1 on a dark ground.
      -->
      <p class="m-0 text-[13px] leading-[21px] text-imio-grey-dark">
        <span i18n:domain="plonemeeting.portal.core" i18n:translate="email_sso_migrated_fallback" tal:omit-tag="">If the button does not work, copy this address into your browser:</span>
        <br>
        <a href="${login_url}" class="break-all text-imio-magenta-dark underline" data-dark="accent">${login_url}</a>
      </p>
    </template>
  </KitMain>
</template>
