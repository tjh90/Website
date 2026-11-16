# HTTP Contract: Recipes

Existing site-wide behaviour applies unchanged: security headers and CSP, `Vary: HX-Request` from
`render()`, no cookies, the site-styled 404 page, and `<h1>` autofocus markup for boosted requests.

## `GET /recipes` (also `HEAD`)

- Route name `recipes`. Responds 200, `text/html`, with the full page (extends `base.html`).
- Query parameters, all optional, parsed into `RecipeQuery`
  ([data-model.md](../data-model.md#recipequery-pydantic-from-query-parameters)):

  | Parameter | Repeatable | Example |
  |---|---|---|
  | `type` | yes | `type=drink&type=side` |
  | `name` | no | `name=spritz` |
  | `ingredient` | no | `ingredient=prosecco` |

- Never returns 4xx for odd values. Unknown types are ignored, and long text is truncated.
- The same full page is returned with or without `HX-Request`. The filter form's htmx request
  selects `#recipe-results` from it (research R8). This also covers boosted navigation, history
  restore and no-JS form submission.
- Default caching (no `Cache-Control` set), as for other GET pages.

### Examples (given the reference collection)

| Request | `#recipe-results` contains |
|---|---|
| `/recipes` | every recipe, status "N recipes" |
| `/recipes?type=drink` | only Drink recipes |
| `/recipes?name=FRENCH` | French 75 |
| `/recipes?ingredient=prosecco` | French 75 (it contains Prosecco as an alternative) |
| `/recipes?ingredient=elderflower%20cordial` | French 75 (an optional ingredient counts) |
| `/recipes?ingredient=limes` | no recipes; status "No matching recipes." |
| `/recipes?type=breakfast&ingredient=gin` | no recipes; message "No matching recipes." |
| `/recipes?type=bogus` | every recipe (the unknown type is ignored) |

## `GET /recipes/{slug}` (also `HEAD`)

- Route name `recipe`. Responds 200 with the full recipe page when `slug` is in the collection.
- Responds 404 with the site's not-found page for any other slug, including one with a different
  case (`/recipes/French-75`).

## Start-up

`create_app()` loads the collection from `Settings.recipes_dir`. If any file is invalid it raises
`RecipeCollectionError` with the full report, so the process does not start serving and the
health check fails. A valid collection is stored on `app.state.recipes`.
