# moreorlessfollowers-cronjobs

Cronjobs for More Or Less Followers. Run on a local machine as a continuous process. This is not yet integrated with the API or backend.

### File structure:

- `main.py` --> main file
- `config.json` --> configuration file, for example:

```json
{
  "amountOfAccounts": 450,
  "amountOfPostsPerAccount": 16,
  "emailToAddress": "myemailaccount@example.com",
  "emailBotAddress": "bot@example.com",
  "cronjobPeriodMinutes": 240,
  "igUsername": "myigaccount123",
  "igPassword": "qwe456",
  "emailBotPassword": "xyz987",
  "backendAuthToken": "abc123",
  "backendBaseURL": "http://mywebserver.com/api"
}
```
