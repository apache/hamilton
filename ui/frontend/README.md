# Apache Hamilton UI frontend

## Dev setup

- If you run against local it should work.
- If you run against prod you need to set up CORS support (https://chrome.google.com/webstore/detail/allow-cors-access-control/lhobafahddgcelffkeicbaginigeejlf). Click enable on the chrome extension
- Set up husky by running: `npm run configure-husky` in the `frontend/` directory

## Code generation

To generate the code for the typescript backend client, run : `npx @rtk-query/codegen-openapi openapi-config.json` from
the `frontend` directory, while the backend is running on localhost:8000.
