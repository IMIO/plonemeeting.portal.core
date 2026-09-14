/**
 * Maizzle project config for `plonemeeting.portal.core`'s own mails.
 *
 * Three imports and one override, which is all a consumer addon's config ever
 * is. The design kit is reached through `./.kit/maizzle.config.base.js`, a file
 * `bin/compile-emails` materialises before every build: in `kit-mode = path` it
 * re-exports the kit inside the installed `imio.emailkit` egg, in
 * `kit-mode = copy` it is the kit itself, copied in. This file cannot tell the
 * two apart, which is the point of the wiring; nothing kit-shaped is vendored
 * here.
 *
 * Note that `package.json` deliberately has no `"type": "module"`. Without it
 * Maizzle loads this file through jiti, which transpiles the ESM syntax it
 * finds, including in the kit file imported below; that file lives outside any
 * npm tree in `path` mode and so has no `package.json` to declare its own
 * module type.
 */
import { defineConfig } from '@maizzle/framework'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

import { kitBaseConfig } from './.kit/maizzle.config.base.js'

const here = dirname(fileURLToPath(import.meta.url))
const kit = kitBaseConfig()

export default defineConfig({
  ...kit,

  output: {
    ...kit.output,
    /** The committed build output, discovered at runtime through emails.zcml. */
    path: resolve(here, '..', 'src', 'plonemeeting', 'portal', 'core', 'templates'),
  },
})
