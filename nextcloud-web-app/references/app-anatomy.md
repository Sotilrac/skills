# Nextcloud app anatomy

Concrete shapes for `packages/nextcloud`. `<appid>` = lowercase id; `<Namespace>` = PHP namespace.

## Layout

```
appinfo/   info.xml, routes.php (returns []), <appid>_*.png screenshots
lib/       AppInfo/Application.php, Controller/, Service/, Exception/
src/       main.ts, App.vue, api/ocs.ts, source/, stores/, style/, views/
tests/     unit/ (PHPUnit), stubs/ (runtime + psalm)
templates/ base PHP template with the mount node
composer.json psalm.xml phpunit.xml .nextcloudignore .editorconfig vite.config.ts
```

Only the built `js/`+`css/` ship; `src/`, `tests/`, `vendor-bin/`, configs are excluded via `.nextcloudignore`.

## info.xml

`<version>` is the source of truth for the tag (`nc-v<version>`). Validate in CI:

```
curl -s https://apps.nextcloud.com/schema/apps/info.xsd -o /tmp/info.xsd
xmllint --schema /tmp/info.xsd packages/nextcloud/appinfo/info.xml --noout
```

Keys: `<id>` (== cert CN == store id), `<name>`, `<summary>`, `<description>` (CDATA), `<version>`, `<licence>`, `<author>`, `<namespace>`, `<category>`, repo/bugs/website, two `<screenshot>` (light+dark), `<dependencies>` (`<php>`, `<nextcloud min/max>`), `<navigations>` → page route. Keep `<nextcloud max-version>` honest — it gates which servers get the app.

## OCS routes (attributes, not routes.php)

```php
#[ApiRoute(verb: 'GET', url: '/files')]
#[ApiRoute(verb: 'GET', url: '/files/{fileId}/raw')]
#[ApiRoute(verb: 'PUT', url: '/files/{fileId}/raw')]
#[FrontpageRoute(verb: 'GET', url: '/')]   // mounts the SPA
```

Controllers stay thin: list folder, return raw text + mtime, write with `If-Match`. No engine.

## OCS DataSource

Same interface as the web sources; the store can't tell them apart.

```ts
export class OcsSource implements DataSource {
  readonly kind = 'ocs';
  readonly canWrite: boolean;   // from NC permission bits
  private mtime: number;

  async read(): Promise<string> {
    const d = await ocs.get<{ content: string; mtime: number }>(`/files/${this.fileId}/raw`);
    this.mtime = d.mtime; return d.content;
  }
  async write(text: string): Promise<void> {
    try {
      const d = await ocs.put<{ mtime: number }>(`/files/${this.fileId}/raw`,
        { content: text }, { 'If-Match': String(this.mtime) });
      this.mtime = d.mtime;
    } catch (e) {
      if (e instanceof OcsError && e.status === 412) throw new WriteConflictError(e.message);
      throw e;
    }
  }
}
```

## Mount

```ts
import { initTooltips, setMetadataSource } from '@shared/ui';
setMetadataSource(new OcsMetadataSource());   // metadata is a folder dotfile
createApp(App).mount('#<appid>-app');
initTooltips({ native: true });               // native title tooltips, not themed
```

A shared tooltip controller can support both modes (themed floater for web, `native` mirroring `data-tooltip`→`title` for NC) so components need no per-host edits.

## PHP tooling

bamarni `composer-bin-plugin` keeps psalm/cs-fixer/phpunit in isolated `vendor-bin/*/vendor` (out of the shipped autoloader).

**psalm.xml** — `lib` only (tests need the psalm-phpunit plugin); stub private `OC\` symbols:

```xml
<projectFiles><directory name="lib"/>
  <ignoreFiles><directory name="vendor"/><directory name="vendor-bin"/></ignoreFiles>
</projectFiles>
<extraFiles><directory name="vendor/nextcloud/ocp"/></extraFiles>
<stubs><file name="tests/stubs/psalm.phpstub"/></stubs>
```

**psalm.phpstub** — unconditional (psalm can't parse `interface_exists()` guards; that's a separate runtime stub):

```php
<?php
namespace OC\Hooks { interface Emitter {} }
namespace OC\User  { class NoUserException extends \Exception {} }
```

**.editorconfig**: `[*.{php,phpstub,xml}]` → `indent_style = tab`.

## Local dev

`dev/docker-compose.yml` with `nextcloud:<major>-apache` (admin/admin, SQLite) + Makefile targets (`nc-validate`, `nc-build`, `nc-dev`). Docker can't add a port to a live container — recreate (`up -d --force-recreate`) if you change the mapping; a named volume keeps data.
