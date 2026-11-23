# The plates from an image (the visualiser in demo/). Run from demo/: `make help`.
#
#   make intake VIEW=torso IMAGE=~/new-torso.png    a new image for a view: checked, installed, the plate built and checked
#   make plate VIEW=hem                             rebuild one plate from its source (silhouette/sources/<view>-straight.png)
#   make plates                                     rebuild all four
#   make check                                      every offline gate (rebuild identical, invariants, frame parity, record, cross-view)
#   make serve                                      the page on http://localhost:8300/testing.html (PORT=...)
#
# A plate is base.jpg + plate.dat (docs/plate.md). It is made from the source image AND the points measured on it, which live in
# silhouette/views/<view>.py. So a new image makes a correct plate by itself only when it shows the form in the same place (a
# re-render with the same camera, a retouch): `intake` tests that first (silhouette/measure/align_check.py) and stops otherwise.
# A different photo needs the view measured again (docs/annotate.md; the Claude Code skill annotate-plate): `make replace` installs
# it anyway and writes the review images to measure from.

PYTHON  ?= python3
NODE    ?= node
PORT    ?= 8300
VARIANT ?= straight
VIEWS   := torso neck sleeve hem

PLATE    = $(VIEW)-$(VARIANT)
SOURCE   = silhouette/sources/$(PLATE).png
PY       = $(PYTHON) -W ignore

.PHONY: help deps intake replace plate plates check rebuild-check xview lace-check serve page-check need-view need-image

help:
	@sed -n '2,14p' Makefile | sed 's/^# \{0,1\}//'
	@echo ""
	@echo "Variables: VIEW=$(VIEWS)  IMAGE=<path>  VARIANT=$(VARIANT)  PORT=$(PORT)  PYTHON=$(PYTHON)  NODE=$(NODE)"
	@echo "Other targets: replace, rebuild-check, xview, lace-check, page-check (needs 'make serve' running), deps"

deps:
	@$(PYTHON) -c "import PIL, sys; print('python', sys.version.split()[0], '+ Pillow', PIL.__version__)" \
	  || { echo "Pillow is missing: $(PYTHON) -m pip install 'pillow>=12.3,<13'"; exit 1; }
	@$(NODE) -e "const v = +process.versions.node.split('.')[0]; console.log('node', process.versions.node + (v < 22 ? '  (page checks need node >= 22)' : ''))" \
	  || echo "node is missing: the frame parity check and the page checks need it"
	@[ -n "$$CHROME" ] && echo "CHROME=$$CHROME" || echo "CHROME is not set: the page checks use the macOS Chrome path by default"

need-view:
	@case " $(VIEWS) " in *" $(VIEW) "*) ;; *) echo "VIEW must be one of: $(VIEWS) (got '$(VIEW)')"; exit 2;; esac

need-image:
	@[ -n "$(IMAGE)" ] || { echo "IMAGE=<path to the new image> is needed"; exit 2; }
	@[ -f "$(IMAGE)" ] || { echo "no such file: $(IMAGE)"; exit 2; }

# The safe path: the image must line up with the one the view was measured on (same size; wall, knob and neck boxes within 2
# levels). Then it replaces the source, the plate is rebuilt (with the review images in review/<plate>/) and checked.
intake: need-view need-image deps
	@echo "== $(PLATE): is $(IMAGE) the same framing as $(SOURCE)?"
	@$(PY) silhouette/measure/align_check.py "$(IMAGE)" "$(SOURCE)" || { \
	  echo ""; \
	  echo "STOP: the new image does not line up with the one silhouette/views/$(VIEW).py was measured on."; \
	  echo "      Its plate would put the fabric and the laces in the wrong places. Nothing was changed."; \
	  echo "      If it is a different photo on purpose: make replace VIEW=$(VIEW) IMAGE=$(IMAGE), then measure the view"; \
	  echo "      again (docs/annotate.md) and run make plate VIEW=$(VIEW)."; \
	  exit 1; }
	cp "$(IMAGE)" "$(SOURCE)"
	$(MAKE) --no-print-directory plate VIEW=$(VIEW)

# The other path: a different photo for the view. It is installed and the review images are written, so that the view can be
# measured on it. The plate built here still uses the OLD measured points: do not ship it before the view is measured again.
replace: need-view need-image deps
	@echo "== $(PLATE): installing $(IMAGE) as the source (the old one stays in git: git checkout -- $(SOURCE) restores it)"
	cp "$(IMAGE)" "$(SOURCE)"
	-$(PY) silhouette/pipeline/make_plate.py assets/plates/$(PLATE) --review
	@echo ""
	@echo "NEXT: the measured points in silhouette/views/$(VIEW).py belong to the old photo. Compare review/$(PLATE)/annotate.png"
	@echo "      with the new photo, measure the view again (docs/annotate.md; tools in silhouette/measure/), then make plate VIEW=$(VIEW)."

plate: need-view deps
	@echo "== $(PLATE): build from $(SOURCE) + silhouette/views/$(VIEW).py"
	$(PY) silhouette/pipeline/make_plate.py assets/plates/$(PLATE) --review
	@$(PY) silhouette/plate.py check $(VIEW) | grep -E '^(FAIL|info  garment fit|ALL PASS|PASS  assets)' \
	  || true
	@echo "== $(PLATE): built (review images in review/$(PLATE)/; a person approves annotate.png and check.png)."
	@echo "   A FAIL above is a defect to look at; StepA's closure items (torso 6 px, sleeve 0.06 %, hem 10 px) are known."

plates: deps
	@for v in $(VIEWS); do $(MAKE) --no-print-directory plate VIEW=$$v || exit 1; done

check: deps rebuild-check xview lace-check
	@for v in $(VIEWS); do $(PY) silhouette/plate.py check $$v || true; done
	$(PY) silhouette/pipeline/platedat.py --check assets/plates/*-$(VARIANT)
	$(PY) silhouette/pipeline/garment.py --check
	$(PY) swatchprep/lace_sidecar.py check assets/swatches/lace-*.json

rebuild-check:
	$(PY) silhouette/plate.py rebuild-check

xview:
	-$(PY) silhouette/checks/xview_check.py

lace-check:
	$(PY) silhouette/checks/xview_lace.py pearl

serve:
	@echo "http://localhost:$(PORT)/testing.html   (Ctrl-C to stop)"
	$(PYTHON) -m http.server $(PORT) --bind 127.0.0.1 --directory .

page-check: need-view
	$(PY) silhouette/plate.py page-check $(VIEW) --port $(PORT)
