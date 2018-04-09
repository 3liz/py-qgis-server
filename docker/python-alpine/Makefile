
BUILDIMAGE=python-gcc:3.6-alpine
BECOME_USER:=$(shell id -u)

package: image
	docker run -it --rm --name python-gcc-$$$$ -u $(BECOME_USER) \
		-v $(HOME)/.alpine/wheels:/wheels \
		-v $(HOME)/.alpine/.cache:/.cache \
		-v $(shell pwd)/requirements.txt:/requirements.txt \
		$(BUILDIMAGE) pip wheel --cache-dir=/.cache -w /wheels -r requirements.txt

image:
	docker image inspect $(BUILDIMAGE) >/dev/null 2>&1 || \
	docker build --rm --force-rm --no-cache -t $(BUILDIMAGE) .



