.PHONY: check serve ask

check:
	python3 -m engine check

serve:
	python3 -m engine serve --open

ask:
	python3 -m engine "$(q)"
