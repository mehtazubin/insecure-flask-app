# unsecure-flask-app

## Running

In order to run this project you need to install two tools:
docker([Windows](https://store.docker.com/editions/community/docker-ce-desktop-windows), [Mac](https://store.docker.com/editions/community/docker-ce-desktop-mac)) [docker-compose](https://github.com/docker/compose/releases/tag/1.19.0)

Once You Install those two, enter these commands from the root directory:

 ```docker-compose up -d --build```

Once the command finishes running with green done message at the end,
Go to the http://localhost:8080/ in your browser to access the app!

If you have already started the app and used the stop command to stop, you can use

```docker-compose start```

to start your saved app from before!

## Stopping

To stop, run this command from the root directory of the project:

```docker-compose stop```

To stop and remove all previous data, run this command from the root directory of the project:

```docker-compose  down```