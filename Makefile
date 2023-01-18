BROWSER=firefox
DCYML=docker/compose.yaml
DCARGS=
HMS=`date +'%H%M%S'`
NETWORK=${PROJECT}_default
PROJECT=chisel
PROXY_COMMAND=mitmproxy
SHINY_SERVER_COMMAND=
WORKDIR=/home/docker

GRID_HOST=chisel_selenium-hub_1
GRID_PORT=4444
PYTESTOPTS=
RESULT_XML=result.xml
COMMAND=pytest \
	    -c tests/pytest.ini \
	    --junitxml=${RESULT_XML} \
	    --driver=Remote \
	    --selenium-host=${GRID_HOST} \
	    --selenium-port=${GRID_PORT} \
	    --capability browserName ${BROWSER} \
	    --verbose \
	    --tb=short \
	    --selene-reports=./screenshots \
	    ${PYTESTOPTS}


.PHONY: all
all:

.PHONY: test-env-up
test-env-up:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		up \
			-d \
			selenium-hub \
			chrome \
			firefox \
			manageritm-server

.PHONY: test-env-down
test-env-down:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		down

.PHONY: test-env-logs
test-env-logs:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		logs \
			--timestamps \
			--follow \
			${DCARGS}

.PHONY: test-env-compose
test-env-compose:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		${DCARGS}

.PHONY: grid-restart
grid-restart:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		restart \
			selenium-hub \
			chrome \
			firefox

.PHONY: proxy-up
proxy-up:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		run \
			--rm \
			--service-ports \
			--name ${PROJECT}_mitmproxy \
			proxy \
			${PROXY_COMMAND}

.PHONY: shiny-server-up
shiny-server-up:
	COMPOSE_DOCKER_CLI_BUILD=1 \
	DOCKER_BUILDKIT=1 \
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		run \
			--rm \
			--service-ports \
			--name ${PROJECT}_shiny-server \
			shiny-server \
			${SHINY_SERVER_COMMAND}

.PHONY: run
run:
	docker-compose \
		-f ${DCYML} \
		-p ${PROJECT} \
		run \
			--rm \
			--name ${PROJECT}_tre_${HMS} \
			--user=`id -u`:`id -g` \
			tre \
			${COMMAND}

.PHONY: clean
clean:
	rm -rf hars/ tmp/ screenshots
	rm -f *.log result.xml
	find . \( -name '*.pyc' -or -name '*.pyo' \) -print -delete
	find . -name '__pycache__' -print -delete

