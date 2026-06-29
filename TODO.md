# TODO

This project only publishes measured CHMI station data into Home Assistant.

## Station Data

- Improve weather condition from station-measured elements when advertised, such
  as 1-hour SYNOP `ww`, `W1`, `W2`, `N`, `VV`, and `Td`.
- Add validation tests for additional station examples.

## Non-Goals

- Text forecast sensors or events.
- Weather alert or warning entities.
- Radar, image, or camera entities.
- Non-station CHMI products.
