VERSION=$(shell cat .version)

build:
	docker build --no-cache src/ --tag talpah/domg:$(VERSION) --tag talpah/domg:latest

push:
	docker push talpah/domg:latest
	docker push talpah/domg:$(VERSION)