# Plan customization

Edit `/etc/pisowifi/plans.json`.

Each plan has:

- `name`
- `minutes`
- `speed_mbps`
- `data_mb`

Example:

```json
"10": {
  "name": "1 Hour",
  "minutes": 60,
  "speed_mbps": 4,
  "data_mb": 700
}
```

The key is the peso amount.

The admin dashboard generates vouchers from these plans.
