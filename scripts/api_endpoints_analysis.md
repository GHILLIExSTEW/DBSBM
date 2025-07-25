# 🏆 Complete API Endpoints Analysis Report
============================================================
📊 Total APIs Analyzed: 12
📈 Total Endpoints Found: 259

## 📈 Overall Statistics
- **Unique Endpoints**: 99
- **Unique Parameters**: 0

## 🏈 AFL API
**Base URL**: `https://v1.afl.api-sports.io`
**Total Endpoints**: 20

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`odds`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

- **`odds/bets`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

- **`odds/bookmakers`**
  - Description: Page 59 ---
bookmakers
Return the list of available bookmakers for odds.

- **`standings`**
  - Description: API Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

### Teams
- **`games/statistics/teams`**
  - Description: CURLOPT_RETURNTRANSFER  => true
  CURLOPT_ENCODING  => ''
  CURLOPT_MAXREDIRS  => 10
  CURLOPT_TIMEOUT  => 0
  CURLOPT_FOLLOWLOCATION  => true
  CURLOPT_HTTP_VERSION  => CURL_HTTP_VERSION_1_1
  CURLOPT_CUSTOMREQUEST  => 'GET'
  CURLOPT_HTTPHEADER  => array
    'x-beta-api-sports-key: XxXxXxXxXxXxXxXxXxXxXxXx'
    'x-rapidapi-host: v1.

- **`teams`**
  - Description: CURLOPT_URL  => 'https://v1.

- **`teams/statistics`**
  - Description: CURLOPT_URL  => 'https://v1.

### Players
- **`games/statistics/players`**
  - Description: CURLOPT_URL  => 'https://v1.

- **`players`**
  - Description: This endpoint requires at least one of theses parameters : id, team, name, search.

- **`players/statistics`**
  - Description: AFL
https://api-sports.

- **`players7/20/25`**
  - Description: This endpoint requires at least one of theses parameters : id, team, name, search.

### Fixtures/Matches
- **`games`**
  - Description: League.

- **`games/events`**
  - Description: Parameters: This endpoint requires at least one of theses parameters : id, ids, date.

- **`games/events7/20/25`**
  - Description: Parameters: This endpoint requires at least one of theses parameters : id, ids, date.

- **`games/quarters`**
  - Description: AFL
https://api-sports.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: You rapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

- **`seasons`**
  - Description: AFL
https://api-sports.

### Utility
- **`timezone`**
  - Description: OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

## 🏈 BASEBALL API
**Base URL**: `https://v1.baseball.api-sports.io`
**Total Endpoints**: 19

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`countries`**
  - Description: CURLOPT_URL  => 'https://v1.

- **`odds`**
  - Description: The id of the bookmaker
integer
The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptcUrlRubyUses Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

- **`odds/bets`**
  - Description: CURLOPT_URL  => 'https://v1.

- **`odds/bookmakers`**
  - Description: CURLOPT_URL  => 'https://v1.

- **`standings`**
  - Description: CURLOPT_RETURNTRANSFER  => true
  CURLOPT_ENCODING  => ''
  CURLOPT_MAXREDIRS  => 10
  CURLOPT_TIMEOUT  => 0
  CURLOPT_FOLLOWLOCATION  => true
  CURLOPT_HTTP_VERSION  => CURL_HTTP_VERSION_1_1
  CURLOPT_CUSTOMREQUEST  => 'GET'
  CURLOPT_HTTPHEADER  => array
    'x-rapidapi-key: XxXxXxXxXxXxXxXxXxXxXxXx'
    'x-rapidapi-host: v1.

- **`standings/groups`**
  - Description: CURLOPT_RETURNTRANSFER  => true
  CURLOPT_ENCODING  => ''
  CURLOPT_MAXREDIRS  => 10
  CURLOPT_TIMEOUT  => 0
  CURLOPT_FOLLOWLOCATION  => true
  CURLOPT_HTTP_VERSION  => CURL_HTTP_VERSION_1_1
  CURLOPT_CUSTOMREQUEST  => 'GET'
  CURLOPT_HTTPHEADER  => array
    'x-rapidapi-key: XxXxXxXxXxXxXxXxXxXxXxXx'
    'x-rapidapi-host: v1.

- **`standings/stages`**
  - Description: CURLOPT_RETURNTRANSFER  => true
  CURLOPT_ENCODING  => ''
  CURLOPT_MAXREDIRS  => 10
  CURLOPT_TIMEOUT  => 0
  CURLOPT_FOLLOWLOCATION  => true
  CURLOPT_HTTP_VERSION  => CURL_HTTP_VERSION_1_1
  CURLOPT_CUSTOMREQUEST  => 'GET'
  CURLOPT_HTTPHEADER  => array
    'x-rapidapi-key: XxXxXxXxXxXxXxXxXxXxXxXx'
    'x-rapidapi-host: v1.

- **`widgets/standings`**
  - Description: By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-baseball-standings
    data-host v1.

### Teams
- **`teams`**
  - Description: The id of the league
integer= 4 characters
The season of the league
string>= 3 characters
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptcUrlRubyUses Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

- **`teams/statistics`**
  - Description: Responses
200 OK
Request samples
PhpPythonNodeJavaScriptcUrlRubyUses Cases
$curl = curl_init
curl_setopt_array $curl array
  CURLOPT_URL  => 'https://v1.

### Fixtures/Matches
- **`games`**
  - Description: T_URL  => 'https://v1.

- **`games/h2h`**
  - Description: CURLOPT_RETURNTRANSFER  => true
  CURLOPT_ENCODING  => ''
  CURLOPT_MAXREDIRS  => 10
  CURLOPT_TIMEOUT  => 0
  CURLOPT_FOLLOWLOCATION  => true
  CURLOPT_HTTP_VERSION  => CURL_HTTP_VERSION_1_1
  CURLOPT_CUSTOMREQUEST  => 'GET'
  CURLOPT_HTTPHEADER  => array
    'x-rapidapi-key: XxXxXxXxXxXxXxXxXxXxXxXx'
    'x-rapidapi-host: v1.

- **`widgets/Games`**
  - Description: If true allows to load a modal containing the standings
string
Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
Request samples
Html
div idwg-api-baseball-games
     data-host v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: Page 35 ---
QUERY PARAMETERS
integer
The id of the league
string
The name of the league
integer
The id of the country
string
The name of the country
string
Enum:"league" "cup"
The type of the league
integer= 4 characters
The season of the league
string>= 3 characters
HEADER PARAMETERS
string
You rapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptcUrlRubyUses Casesid
name
country_id
country
type
season
search
x-rapidapi-key
required
GET/leagues7/20/25, 9:21 PM API-Sports - Documentation Baseball
https://api-sports.

- **`leagues7/20/25`**
  - Description: Page 35 ---
QUERY PARAMETERS
integer
The id of the league
string
The name of the league
integer
The id of the country
string
The name of the country
string
Enum:"league" "cup"
The type of the league
integer= 4 characters
The season of the league
string>= 3 characters
HEADER PARAMETERS
string
You rapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptcUrlRubyUses Casesid
name
country_id
country
type
season
search
x-rapidapi-key
required
GET/leagues7/20/25, 9:21 PM API-Sports - Documentation Baseball
https://api-sports.

- **`seasons`**
  - Description: CURLOPT_URL  => 'https://v1.

### Utility
- **`timezone`**
  - Description: PM API-Sports - Documentation Baseball
https://api-sports.

## 🏈 BASKETBALL API
**Base URL**: `https://v1.basketball.api-sports.io`
**Total Endpoints**: 22

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`bets`**
  - Description: Example:search=under
The name of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`bookmakers`**
  - Description: ETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`countries`**
  - Description: OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings`**
  - Description: YYYY or YYYY-YYYY
Example:season=2021-2022
The season of the league
integer
The id of the team
string
Example:stage=NBA - Regular Season
A valid stage
string
Example:group=Eastern Conference
A valid group
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequestleague
required
season
required
team
stage
group
x-rapidapi-key
required
GET/standings
Copy
\
;
\
\
;7/20/25, 9:21 PM API-Sports - Documentation Basketball
https://api-sports.

- **`standings/groups`**
  - Description: OK
—201 Created
 Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/stages`**
  - Description: The season of the league
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/standings`**
  - Description: PM API-Sports - Documentation Basketball
https://api-sports.

### Teams
- **`games/statistics/teams`**
  - Description: Use Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams`**
  - Description: ER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Players
- **`games/statistics/players`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`players`**
  - Description: This endpoint requires at least one parameter.

- **`players7/20/25`**
  - Description: This endpoint requires at least one parameter.

### Fixtures/Matches
- **`games`**
  - Description: Client
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/h2h7/20/25`**
  - Description: QUERY PARAMETERS
stringid-id
Example:h2h=132-134
The ids of the teams
stringYYYY-MM-DD
Example:date=2019-12-05
A valid date
integer
The id of the league
string[ 4 .

- **`widgets/Games`**
  - Description: Page 26 ---
Request samples
Html
div idwg-api-basketball-games
     data-host v1.

### Statistics
- **`statistics`**
  - Description: PythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: Page 36 ---
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Page 31 ---
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Utility
- **`timezone`**
  - Description: Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

## 🏈 FOOTBALL DOCUMENTATION API
**Base URL**: `https://v3.football.api-sports.io`
**Total Endpoints**: 46

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`coachs`**
  - Description: Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get coachs from one coach {id}
get"https://v3.

- **`countries`**
  - Description: QUERY PARAMETERS
string
The name of the country
string[ 2 .

- **`injuries`**
  - Description: It’s possible to make requests by mixing the available parameters
get"https://v3.

- **`odds`**
  - Description: In this endpoint the "season" parameter is .

- **`odds/bets`**
  - Description: ADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available bets
get"https://v3.

- **`odds/bookmakers`**
  - Description: Page 137 ---
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available bookmakers
get"https://v3.

- **`odds/live`**
  - Description: In this endpoint the "season" parameter is .

- **`odds/live/bets`**
  - Description: Page 126 ---
QUERY PARAMETERS
string
The id of the bet name
string= 3 characters
The name of the bet
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available bets
get"https://v3.

- **`odds/mapping`**
  - Description: Time Out
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

- **`predictions`**
  - Description: The id of the fixture
HEADER PARAMETERSfixture
required7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`sidelined`**
  - Description: HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all from one {player}
get"https://v3.

- **`standings`**
  - Description: Recommended Calls : 1 call per hour for the leagues or teams who have at least one fixture in progress
otherwise 1 call per day.

- **`standings7/20/25`**
  - Description: Recommended Calls : 1 call per hour for the leagues or teams who have at least one fixture in progress
otherwise 1 call per day.

- **`transfers`**
  - Description: Page 115 ---
integer
The id of the player
integer
The id of the team
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all transfers from one {player}
get"https://v3.

- **`trophies`**
  - Description: Page 117 ---
integer
The id of the player
stringMaximum of 20 players ids
Value:"id-id-id"
One or more players ids
integer
The id of the coach
stringMaximum of 20 coachs ids
Value:"id-id-id"
One or more coachs ids
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRubyplayer
players
coach
coachs
x-rapidapi-key
required
GET/trophies
Copy7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`venues`**
  - Description: Old Trafford"
// Get all venues from {city}
get"https://v3.

- **`widgets/standings`**
  - Description: If you leave the field empty, the default  theme will be applied, otherwise the
possible values are grey or dark
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-football-standings
    data-host v3.

### Teams
- **`players/teams`**
  - Description: QUERY PARAMETERS
integer
The id of the player
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Errorplayer
required
x-rapidapi-key
required7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`teams`**
  - Description: Get teams from one team {country}
get"https://v3.

- **`teams/countries`**
  - Description: Recommended Calls : 1 call per day.

- **`teams/seasons`**
  - Description: RS
integer
The id of the team
HEADER PARAMETERS
string
Your Api-Key
Responsesteam
required
x-rapidapi-key
required7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`teams/statistics`**
  - Description: Documentation
https://www.

### Players
- **`fixtures/players`**
  - Description: Page 81 ---
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
 Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available players statistics from one {fixture}
get"https://v3.

- **`players`**
  - Description: Page 91 ---
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all seasons available for players endpoint
get"https://v3.

- **`players/profiles`**
  - Description: Allows you to search for a player in relation to a player {lastname}
get"https://v3.

- **`players/seasons`**
  - Description: Page 91 ---
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all seasons available for players endpoint
get"https://v3.

- **`players/squads`**
  - Description: OKteam
player
x-rapidapi-key
required7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`players/topassists`**
  - Description: Client
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

- **`players/topredcards`**
  - Description: YYYY
The season of the league
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

- **`players/topscorers`**
  - Description: YYYY
The season of the league
HEADER PARAMETERS
string
Your Api-Key
Responses
200 OK
204 No Content
499 Time Out
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

- **`players/topyellowcards`**
  - Description: The player that played the fewer minutes
Update Frequency : This endpoint is updated several times a week.

- **`players/topyellowcards7/20/25`**
  - Description: The player that played the fewer minutes
Update Frequency : This endpoint is updated several times a week.

- **`players7/20/25`**
  - Description: Page 97 ---
QUERY PARAMETERS
integer
The id of the player
integer
The id of the team
integer
The id of the league
integer= 4 charactersYYYY | Requires the fields Id, League or Team.

### Fixtures/Matches
- **`fixtures`**
  - Description: Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available rounds from one {league} & {season}
get"https://v3.

- **`fixtures/events`**
  - Description: Get all available events from one {fixture} & {type}
get"https://v3.

- **`fixtures/headtohead`**
  - Description: Response samples
200 204 499 500GET/fixtures/headtohead
Copy
(
)
;
(
)
;
(
)
(
(
(
(
(
application/json
Expand allCollapse all Copy
{
"get": "fixtures/headtohead"
,
"parameters" : -
{
"h2h": "33-34"
,
"last": "1"
}
,
"errors" :
[ ]
,
"results" : 1
,Content type7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`fixtures/lineups`**
  - Description: Get all available lineups from one {fixture} & {type}
get"https://v3.

- **`fixtures/rounds`**
  - Description: Use CasesPhpPythonNodeJavaScriptCurlRuby
// Get all available rounds from one {league} & {season}
get"https://v3.

- **`fixtures/statistics`**
  - Description: Get all available statistics from one {fixture} with Fulltime, First & Second
get"https://v3.

- **`widgets/Games7/20/25`**
  - Description: If true allows to load a modal containing all the details of the game
string
Enum:truefalse
If true allows to load a modal containing the standings
string
Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errorsdata-date
data-league
data-season
data-theme
data-show-toolbar
data-show-logos
data-modal-game
data-modal-standings
data-modal-show-logos
data-show-errors
GET/widgets/Games7/20/25, 9:21 PM API-Football - Documentation
https://www.

- **`widgets/game`**
  - Description: PM API-Football - Documentation
https://www.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: Get all leagues from one {country}
// You can find the available {country} by using the endpoint country
get"https://v3.

- **`leagues/seasons`**
  - Description: Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

### Utility
- **`timezone`**
  - Description: Time Out
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v3.

## 🏈 FORMULA_1 API
**Base URL**: `https://v1.formula-1.api-sports.io`
**Total Endpoints**: 18

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`circuits`**
  - Description: Formula-1
https://api-sports.

- **`circuits7/20/25`**
  - Description: Formula-1
https://api-sports.

- **`drivers`**
  - Description: DER PARAMETERS
string
Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`pitstop`**
  - Description: QUERY PARAMETERS
integer
The id of the race
integer
The id of the team
integer
The id of the driver
HEADER PARAMETERS
string
Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`pitstops`**
  - Description: QUERY PARAMETERS
integer
The id of the race
integer
The id of the team
integer
The id of the driver
HEADER PARAMETERS
string
Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`races`**
  - Description: Sprint" "1st Sprint Shootout"
 "2nd Sprint
Shootout" "3rd Sprint Shootout" "1st Practice"
 "2nd
Practice" "3rd Practice"
The type of the race
string
Example:timezone=Europe/London
A valid timezone
HEADER PARAMETERS
string
Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`rankings`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation Formula-1
https://api-sports.

- **`rankings/drivers`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`rankings/fastestlaps`**
  - Description: Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`rankings/races`**
  - Description: Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`rankings/startinggrid`**
  - Description: PythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Teams
- **`rankings/teams7/20/25`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation Formula-1
https://api-sports.

- **`teams`**
  - Description: Page 33 ---
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`competitions`**
  - Description: Your API-Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Page 26 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Utility
- **`timezone`**
  - Description: Page 24 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

## 🏈 HANDBALL API
**Base URL**: `https://v1.handball.api-sports.io`
**Total Endpoints**: 18

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`countries`**
  - Description: Page 33 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: Page 54 ---
Odds are updated once a day
QUERY PARAMETERS
integer
The id of the league
integer= 4 characters
The season of the league
integer
The id of the game
integer
The id of the bookmaker
integer
The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequestleague
season
game
bookmaker
bet
x-rapidapi-key
required
GET/odds
Copy
\
;
\
\
;7/20/25, 9:20 PM API-Sports - Documentation Handball
https://api-sports.

- **`odds/bets`**
  - Description: The name of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: The name of the bookmaker
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings`**
  - Description: To know the list of available stages or groups you have to use the endpoint standings/stages or
standings/groups
Standings are updated every hours
QUERY PARAMETERS
integer
The id of the league
integer= 4 characters
The season of the league
integer
The id of the team
string
A valid stage
string
A valid group
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Casesleague
required
season
required
team
stage
group
x-rapidapi-key
required
GET/standings
Copy7/20/25, 9:20 PM API-Sports - Documentation Handball
https://api-sports.

- **`standings/groups`**
  - Description: OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/stages`**
  - Description: Y PARAMETERS
integer
The id of the league
string= 4 characters
The season of the league
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/standings`**
  - Description: By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-handball-standings
    data-host v1.

### Teams
- **`teams`**
  - Description: The id of the league
integer= 4 characters
The season of the league
string>= 3 characters
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams/statistics`**
  - Description: Client
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Fixtures/Matches
- **`games`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/h2h`**
  - Description: NodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/Games`**
  - Description: If true allows to load a modal containing the standings
string
Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
Request samples
Html
div idwg-api-handball-games
     data-host v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Page 30 ---
Seasons
seasons
All seasons are only 4-digit keys, so for a league whose season is 2018-2019  the season in the API will
be 2018.

### Utility
- **`timezone`**
  - Description: PM API-Sports - Documentation Handball
https://api-sports.

## 🏈 HOCKEY API
**Base URL**: `https://v1.hockey.api-sports.io`
**Total Endpoints**: 21

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`countries`**
  - Description: Page 32 ---
countries
Get the list of available countries.

- **`countries7/20/25`**
  - Description: Page 32 ---
countries
Get the list of available countries.

- **`odds`**
  - Description: The season of the league
integer
The id of the game
integer
The id of the bookmaker
integer
The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bets`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: Page 61 ---
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/groups`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/stages`**
  - Description: Hockey
https://api-sports.

- **`standings/stages7/20/25`**
  - Description: Hockey
https://api-sports.

- **`widgets/standings`**
  - Description: By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-hockey-standings
    data-host v1.

### Teams
- **`teams`**
  - Description: The id of the league
integer= 4 characters
The season of the league
string>= 3 characters
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams/statistics`**
  - Description: Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Fixtures/Matches
- **`games`**
  - Description: Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/events`**
  - Description: NodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/h2h`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/Games`**
  - Description: If true allows to load a modal containing the standings
string
Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
Request samples
Html
div idwg-api-hockey-games
     data-host v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: I Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Hockey
https://api-sports.

### Utility
- **`timezone`**
  - Description: PM API-Sports - Documentation Hockey
https://api-sports.

## 🏈 MMA API
**Base URL**: `https://v1.mma.api-sports.io`
**Total Endpoints**: 15

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`categories`**
  - Description: Page 27 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: Default:"YYYY-MM-DD"
Example:date=2023-08-26
A valid date
integer
The id of the bookmaker
integer
The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bets`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: All bookmakers id can be used in endpoint odds as filters.

### Teams
- **`teams`**
  - Description: Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Fixtures/Matches
- **`fighters`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`fighters/records`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`fights`**
  - Description: Page 36 ---
string
Default:"YYYY-MM-DD"
Example:date=2023-08-26
A valid date
integer
Default:"YYYY"
Example:season=2023
A valid season
integer
The id of the fighter
string
Example:category=Flyweight
The name of the category
string
Example:timezone=Europe/London
A valid timezone
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Casesdate
season
fighter
category
timezone
x-rapidapi-key
required
GET/fights
Copy7/20/25, 9:20 PM API-Sports - Documentation MMA
https://api-sports.

- **`fights/results`**
  - Description: Use Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`fights/results/`**
  - Description: Use Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`fights/statistics/fighters`**
  - Description: Use Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`seasons`**
  - Description: Page 25 ---
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Utility
- **`timezone`**
  - Description: Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

## 🏈 NBA API
**Base URL**: `https://v2.nba.api-sports.io`
**Total Endpoints**: 19

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`standings`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`standings/`**
  - Description: XxXxXxXx'
$client->enqueue $request ->send
$response  = $client->getResponse
echo $response ->getBody
Response samples
200GET/standings
Copy
\
;
\
\
;
(
)
;
(
)
;
(
\
(
(
,
)
)
)
;
(
(
,
)
)
;
(
)
(
)
;
(
)
;
(
)
;
application/jsonContent type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

### Teams
- **`teams`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`teams/`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

- **`teams/statistics`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

- **`teams/statistics7/20/25`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

### Players
- **`players`**
  - Description: Example:search=Jame
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`players/`**
  - Description: RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`players/statistics`**
  - Description: RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

### Fixtures/Matches
- **`games`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`games/`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

- **`games/statistics`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

- **`games/statistics7/20/25`**
  - Description: Content type7/20/25, 9:20 PM API-Sports - Documentation NBA
https://api-sports.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: You rapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`leagues/`**
  - Description: GET'
$request ->setHeaders array
'x-rapidapi-host'  => 'v2.

- **`seasons`**
  - Description: Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v2.

- **`seasons/`**
  - Description: T'
$request ->setHeaders array
'x-rapidapi-host'  => 'v2.

## 🏈 NFL_&_NCAA API
**Base URL**: `https://v1.american-football.api-sports.io`
**Total Endpoints**: 23

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`injuries`**
  - Description: The id of the team
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
401 Unauthorized
404 Not Found
429 Too Many Requests
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bets`**
  - Description: Page 61 ---
 Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: All bookmakers id can be used in endpoint odds as filters.

- **`standings`**
  - Description: Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/conferences`**
  - Description: NFL & NCAA
https://api-sports.

- **`standings/divisions`**
  - Description: The id of the league
integer
Default:"YYYY"
The season of the league
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
401 Unauthorized
404 Not Found
429 Too Many Requests
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Teams
- **`games/statistics/teams`**
  - Description: JavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Players
- **`games/statistics/players`**
  - Description: Page 47 ---
QUERY PARAMETERS
integer
The id of the game
string
Enum:"defensive" "fumbles" "interceptions" "kick_returns"
"kicking" "passing" "punt_returns" "punting" "receiving"
"rushing"
A valid group
integer
The id of the team
integer
The id of the player
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
401 Unauthorized
404 Not Found
429 Too Many Requests
500 Internal Server Error
Request samplesid
required
group
team
player
x-rapidapi-key
required
GET/games/statistics/players7/20/25, 9:19 PM API-Sports - Documentation NFL & NCAA
https://api-sports.

- **`games/statistics/players7/20/25`**
  - Description: Page 47 ---
QUERY PARAMETERS
integer
The id of the game
string
Enum:"defensive" "fumbles" "interceptions" "kick_returns"
"kicking" "passing" "punt_returns" "punting" "receiving"
"rushing"
A valid group
integer
The id of the team
integer
The id of the player
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
401 Unauthorized
404 Not Found
429 Too Many Requests
500 Internal Server Error
Request samplesid
required
group
team
player
x-rapidapi-key
required
GET/games/statistics/players7/20/25, 9:19 PM API-Sports - Documentation NFL & NCAA
https://api-sports.

- **`players`**
  - Description: PM API-Sports - Documentation NFL & NCAA
https://api-sports.

- **`players/statistics`**
  - Description: CurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`players7/20/25`**
  - Description: PM API-Sports - Documentation NFL & NCAA
https://api-sports.

### Fixtures/Matches
- **`games`**
  - Description: PM API-Sports - Documentation NFL & NCAA
https://api-sports.

- **`games/events`**
  - Description: Client
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games7/20/25`**
  - Description: PM API-Sports - Documentation NFL & NCAA
https://api-sports.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: API and competitions keep it across all seasons
This endpoint contains a field named coverage  that indicates for each season of a competition the data
that are available.

- **`leagues7/20/25`**
  - Description: API and competitions keep it across all seasons
This endpoint contains a field named coverage  that indicates for each season of a competition the data
that are available.

- **`seasons`**
  - Description: Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Utility
- **`timezone`**
  - Description: Requests
500 Internal Server Error
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

## 🏈 RUGBY API
**Base URL**: `https://v1.rugby.api-sports.io`
**Total Endpoints**: 19

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`countries`**
  - Description: Page 33 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: Page 53 ---
QUERY PARAMETERS
integer
The id of the league
integer= 4 characters
The season of the league
integer
The id of the game
integer
The id of the bookmaker
integer
The id of the bet
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bets`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: Get all available bookmakers.

- **`standings`**
  - Description: To know the list of available stages or groups you have to use the endpoint standings/stages or
standings/groups
Standings are updated every hours
QUERY PARAMETERS
integer
The id of the league
integer= 4 characters
The season of the league
integer
The id of the team
string
A valid stage
string
A valid group
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samplesleague
required
season
required
team
stage
group
x-rapidapi-key
required
GET/standings7/20/25, 9:19 PM API-Sports - Documentation Rugby
https://api-sports.

- **`standings/groups`**
  - Description: Rugby
https://api-sports.

- **`standings/stages`**
  - Description: Page 45 ---
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings7/20/25`**
  - Description: To know the list of available stages or groups you have to use the endpoint standings/stages or
standings/groups
Standings are updated every hours
QUERY PARAMETERS
integer
The id of the league
integer= 4 characters
The season of the league
integer
The id of the team
string
A valid stage
string
A valid group
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samplesleague
required
season
required
team
stage
group
x-rapidapi-key
required
GET/standings7/20/25, 9:19 PM API-Sports - Documentation Rugby
https://api-sports.

- **`widgets/standings`**
  - Description: By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-rugby-standings
    data-host v1.

### Teams
- **`teams`**
  - Description: The season of the league
string>= 3 characters
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams/statistics`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

### Fixtures/Matches
- **`games`**
  - Description: OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/h2h`**
  - Description: PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/Games`**
  - Description: Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
Request samples
Html
div idwg-api-rugby-games
     data-host v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: Page 36 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Rugby
https://api-sports.

### Utility
- **`timezone`**
  - Description: PM API-Sports - Documentation Rugby
https://api-sports.

## 🏈 VOLLEYBALL API
**Base URL**: `https://v1.volleyball.api-sports.io`
**Total Endpoints**: 19

### Core Data
- **`: `**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

- **`countries`**
  - Description: Page 33 ---
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds`**
  - Description: RubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bets`**
  - Description: Page 56 ---
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`odds/bookmakers`**
  - Description: HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings`**
  - Description: The season of the league
integer
The id of the team
string
A valid stage
string
A valid group
HEADER PARAMETERS
string
Your RapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/groups`**
  - Description: OK
 Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`standings/stages`**
  - Description: API Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRuby
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/standings`**
  - Description: By default false, used for debugging, with a value of true it allows to
display the errors
string
Enum:truefalse
If true display teams logos
Request samples
Html
div idwg-api-volleyball-standings
    data-host v1.

### Teams
- **`teams`**
  - Description: Page 38 ---
You can find all the leagues ids on our Dashboard.

- **`teams/statistics`**
  - Description: Client
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`teams7/20/25`**
  - Description: Page 38 ---
You can find all the leagues ids on our Dashboard.

### Fixtures/Matches
- **`games`**
  - Description: NodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`games/h2h`**
  - Description: JavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`widgets/Games`**
  - Description: If true allows to load a modal containing the standings
string
Enum:truefalse
If true display teams logos and players images in the modal
string
Enum:truefalse
By default false, used for debugging, with a value of true it allows to
display the errors
Request samples
Html
div idwg-api-volleyball-games
     data-host v1.

### Statistics
- **`status`**
  - Description: It allows you to:
To follow your consumption in real time
Manage your subscription and change it if necessary
Check the status of our servers
Test all endpoints without writing a line of code.

### Leagues/Competitions
- **`leagues`**
  - Description: HEADER PARAMETERS
string
You rapidAPI Key
Responses
200 OK
Request samples
PhpPythonNodeJavaScriptCurlRubyUse Cases
$client = new httpClient
$request  = new httpClientRequest
$request ->setRequestUrl 'https://v1.

- **`seasons`**
  - Description: Page 30 ---
Seasons
seasons
All seasons are only 4-digit keys, so for a league whose season is 2018-2019  the season in the API will
be 2018.

### Utility
- **`timezone`**
  - Description: PM API-Sports - Documentation Volleyball
https://api-sports.

## 🔄 Common Endpoints Across APIs
- **`: `**: Football Documentation, AFL, Baseball, Basketball, Formula_1, Handball, Hockey, MMA, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`countries`**: Football Documentation, Baseball, Basketball, Handball, Hockey, Rugby, Volleyball
- **`injuries`**: Football Documentation, NFL_&_NCAA
- **`leagues`**: Football Documentation, AFL, Baseball, Basketball, Handball, Hockey, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`odds`**: Football Documentation, AFL, Baseball, Basketball, Handball, Hockey, MMA, NFL_&_NCAA, Rugby, Volleyball
- **`odds/bets`**: Football Documentation, AFL, Baseball, Handball, Hockey, MMA, NFL_&_NCAA, Rugby, Volleyball
- **`odds/bookmakers`**: Football Documentation, AFL, Baseball, Handball, Hockey, MMA, NFL_&_NCAA, Rugby, Volleyball
- **`players`**: Football Documentation, AFL, Basketball, NBA, NFL_&_NCAA
- **`players7/20/25`**: Football Documentation, AFL, Basketball, NFL_&_NCAA
- **`standings`**: Football Documentation, AFL, Baseball, Basketball, Handball, Hockey, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`standings7/20/25`**: Football Documentation, Rugby
- **`status`**: Football Documentation, AFL, Baseball, Basketball, Formula_1, Handball, Hockey, MMA, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`teams`**: Football Documentation, AFL, Baseball, Basketball, Formula_1, Handball, Hockey, MMA, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`teams/statistics`**: Football Documentation, AFL, Baseball, Handball, Hockey, NBA, Rugby, Volleyball
- **`timezone`**: Football Documentation, AFL, Baseball, Basketball, Formula_1, Handball, Hockey, MMA, NFL_&_NCAA, Rugby, Volleyball
- **`widgets/standings`**: Football Documentation, Baseball, Basketball, Handball, Hockey, Rugby, Volleyball
- **`games`**: AFL, Baseball, Basketball, Handball, Hockey, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`games/events`**: AFL, Hockey, NFL_&_NCAA
- **`games/statistics/players`**: AFL, Basketball, NFL_&_NCAA
- **`games/statistics/teams`**: AFL, Basketball, NFL_&_NCAA
- **`players/statistics`**: AFL, NBA, NFL_&_NCAA
- **`seasons`**: AFL, Baseball, Basketball, Formula_1, Handball, Hockey, MMA, NBA, NFL_&_NCAA, Rugby, Volleyball
- **`games/h2h`**: Baseball, Handball, Hockey, Rugby, Volleyball
- **`leagues7/20/25`**: Baseball, NFL_&_NCAA
- **`standings/groups`**: Baseball, Basketball, Handball, Hockey, Rugby, Volleyball
- **`standings/stages`**: Baseball, Basketball, Handball, Hockey, Rugby, Volleyball
- **`widgets/Games`**: Baseball, Basketball, Handball, Hockey, Rugby, Volleyball

## 📋 Parameter Analysis
