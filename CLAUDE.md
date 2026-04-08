# home-assistant-hellofresh

HACS custom component for Home Assistant. Polls the HelloFresh UK API via `pyhellofresh-uk` and exposes two sensor entities.

## Project layout

```
custom_components/hellofresh/
  manifest.json      # HA manifest — version, requirements (pyhellofresh-uk==x.y.z), iot_class
  const.py           # Domain + config entry key constants
  config_flow.py     # UI config flow (email, password, optional FlareSolverr URL)
  coordinator.py     # DataUpdateCoordinator[HelloFreshData] — fetches both sensors' data
  sensor.py          # Two sensor entities
  strings.json       # Translation source (entity names, config flow labels/errors)
  translations/en.json  # English translations (must mirror strings.json — HA frontend uses this)
hacs.json            # HACS metadata
```

## Sensors

### `sensor.hellofresh_last_delivery`
- **State**: number of meals in the most recently delivered box
- **Unit**: `meals`
- **Attributes**: `week` (ISO week string), `meals` (list of `{name, headline, image_url, website_url, pdf_url, category}`)

### `sensor.hellofresh_next_delivery`
- **State**: `SensorDeviceClass.TIMESTAMP` — the **delivery datetime** of the next scheduled delivery
- **Attributes**: `week`, `status`, `cutoff_date`, `delivery_date`, `meals`

### `sensor.hellofresh_next_changeable_delivery`
- **State**: `SensorDeviceClass.TIMESTAMP` — the **cutoff datetime** (deadline to change the order)
- **Attributes**: `week`, `cutoff_date`, `delivery_date`, `meals` (currently selected meals)
- Returns `None` when all upcoming deliveries are past their cutoff

## Coordinator data model

```python
@dataclass
class HelloFreshData:
    last_delivery: WeeklyDelivery | None       # from get_last_delivery()
    next_delivery: UpcomingDelivery | None     # from get_upcoming_delivery()
    next_changeable: UpcomingDelivery | None   # from get_next_changeable_delivery() (or reuses next_delivery if cutoff not yet passed)
```

## Config entry data keys

Defined in `const.py`:

| Key | Description |
|-----|-------------|
| `email` | HelloFresh account email |
| `password` | Account password (stored in HA secrets) |
| `flaresolverr_url` | Optional FlareSolverr instance URL |
| `subscription_id` | Active subscription ID (int) |
| `customer_plan_id` | First entry from `customerPlanIds` — needed for menu API |
| `customer_uuid` | UUID used as device identifier and unique_id prefix |
| `refresh_token` | Stored for token refresh on restart |

## Library dependency

The component requires `pyhellofresh-uk`. Version is pinned in `manifest.json` under `requirements`. When bumping the library version, update both `manifest.json` and reinstall in the HA devcontainer.

New config entries populate `customer_plan_id` automatically. Existing entries (created before v0.1.5) will have an empty `customer_plan_id`, so the Next Delivery sensor will return `None` until the entry is re-created.

## Translations

Both `strings.json` and `translations/en.json` must be kept in sync — HA loads `translations/en.json` at runtime for the frontend. `strings.json` is the source of truth for the backend/config flow.

## HACS

`hacs.json` sets `content_in_root: false` (component is under `custom_components/`). Minimum HA version: `2024.1.0`.
