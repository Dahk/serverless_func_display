from IPython.display import display, HTML, Javascript
import math, time

class MassiveDisplay():
    def __init__(self, idlist):
        self.progressTracker = {
            bar_id : 0
            for bar_id in idlist
        }
        self.metrics_max = 5
        self.count = len(idlist)
        self.stages = [self.count, 0, 0, 0]
        self.end_stage = len(self.stages)-1
        self.slowest_per_stage = [0, 0, 0]
        self.frame_delay = 1
        self.frame_start = 0
        self.update_scale = False
        self.render_buffer = ''
        self.css = """
        <style>
        .upper-bars {
            display: grid;
            grid-template-rows: repeat({NUM_ROWS}, 6px);
            grid-template-columns: repeat({NUM_COLS}, 1fr);
            background-color: #EEE;
            border: 0;
            border-radius: 12px;
            position: relative;
            box-shadow: 0 75px 125px -57px #7e8f94;
            padding: 4px;
        }
        .gantt-row-bars {
            display: grid;
            grid-template-columns: repeat(100, 1fr);
            grid-template-rows: auto;
            margin-bottom: 1px;
            margin-top: 1px;
            position: relative;
            background-color: #C0C5CE;
            border-radius: 14px;
            width: auto;
            margin-left: 3px;
            margin-right: 3px;
        }
        .gantt-row-bars > div {
            background-color: #3aabe8;
            color: #fff;
            border-radius: 14px;
        }
        .stages {
            display: grid;
            position: relative;
            background-color: #EEE;
            border: 0;
            border-radius: 12px;
            box-shadow: 0 75px 125px -57px #7e8f94;
            margin: 10px 20%;
            height: 325px;
            padding: 15px 0px;
        }
        .stage-bar {
            display: grid;
            grid-template-columns: repeat({NUM_WORKERS}, 1fr);
            grid-template-rows: auto;
            position: relative;
            background-color: #D1D6DF;
            border-radius: 10px;
            width: auto;
            margin: 15px 25px;
            padding: 1px 1px;
        }
        .stage-bar > span {
            position: absolute; 
            z-index: 1;
            left: 50%;
            margin-left: -10%;
            top: 30%;
            font-weight: bold;
            font-size: 16px;
            font-family: sans-serif;
            color: #FFF;
            text-shadow: 0.5px 0.5px 0 #333;
        }
        .stage-bar > div {
            color: #fff;
            border-radius: 10px;
            position: relative;
            height: 100%;
        }
        </style>
        """
        self.html_row_template = """
        <div id="row_id_{ID}" class="gantt-row-bars" style="grid-column: {COL}; grid-row: {ROW};">
            <div id="bar_id_{ID}" style="grid-column: 1; display: none"></div>
        </div>
        """
        self.html_template = """
        <div style="background-color: #cddade; padding: 30px;">
        <div class="upper-bars">
            {ROWS}
        </div>
        <div class="stages">
            <div class="stage-bar">
                <span style="left: 0; margin-left: 5px;">Fetching</span>
                <span id="stage0-text">{NUM_WORKERS}/{NUM_WORKERS} (100%)</span>
                <span id="stage0-timestamp" style="left: 97.5%;"></span>
                <div id="stage0-bar" style="grid-column: 1/{NUM_WORKERS_PLUS1}; background-color: #034561;"></div>
            </div>
            <div class="stage-bar">
                <span style="left: 0; margin-left: 5px;">Processing</span>
                <span id="stage1-text">0/{NUM_WORKERS} (0%)</span>
                <span id="stage1-timestamp" style="left: 97.5%;"></span>
                <div id="stage1-bar" style="grid-column: 1/1; display: none; background-color: #409d9b;"></div>
            </div>
            <div class="stage-bar">
                <span style="left: 0; margin-left: 5px;">Uploading results</span>
                <span id="stage2-text">0/{NUM_WORKERS} (0%)</span>
                <span id="stage2-timestamp" style="left: 97.5%;"></span>
                <div id="stage2-bar" style="grid-column: 1/1; display: none; background-color: #4fb783;"></div>
            </div>
            <div class="stage-bar">
                <span style="left: 0; margin-left: 5px;">Finished</span>
                <span id="stage3-text">0/{NUM_WORKERS} (0%)</span>
                <span id="stage3-timestamp" style="left: 97.5%;"></span>
                <div id="stage3-bar" style="grid-column: 1/1; display: none; background-color: #8cd154;"></div>
            </div>
        </div>
        </div>
        """
        self.js_update_bar = """

        var elem = document.getElementById("bar_id_{ID}")
        var part = {PART}
        elem.style.gridColumn = "1/" + part
        if (part > 1) elem.style.display = "block"
        """
        self.js_complete_bar = """

        var elem = document.getElementById("bar_id_{ID}")
        elem.style.backgroundColor = "#1abc9c"
        """
        self.js_update_stage = """

        var elem = document.getElementById("stage{STAGE}-bar")
        var part = {PART}
        if (part){
            elem.style.gridColumn = "1/" + (part+1)
            elem.style.display = "block"
        } else
            elem.style.display = "none"
        elem = document.getElementById("stage{STAGE}-text")
        elem.innerHTML = part + "/{NUM_WORKERS} (" + (part / {NUM_WORKERS} * 100).toFixed(2) + "%)"
        """.replace('{NUM_WORKERS}', str(self.count))
        self.js_update_timestamp = """

        var elem = document.getElementById("stage{STAGE}-timestamp")
        elem.innerHTML = "{TIME}s"
        """
        
    def show(self):
        num_rows = self.count
        num_cols = 5
        if num_rows > 1024:
            num_cols = 10
        elif num_rows > 512:
            num_cols = 8
        rows_per_col = math.trunc(num_rows / num_cols)
        spare_rows = num_rows % num_cols
        added_extra_row = 1 if spare_rows else 0
        rows = ''
        iter_ids = iter(self.progressTracker.keys())
        for col in range(1, num_cols+1):
            col_template = self.html_row_template.replace('{COL}', str(col))
            for r in range(0, rows_per_col):
                rows = rows + col_template.replace('{ID}', str(next(iter_ids))).replace('{ROW}', str(r+1))
            if spare_rows:
                rows = rows + col_template.replace('{ID}', str(next(iter_ids))).replace('{ROW}', str(rows_per_col+1))
                spare_rows -= 1

        html = self.html_template.replace('{ROWS}', rows)\
               .replace('{NUM_WORKERS}', str(self.count)).replace('{NUM_WORKERS_PLUS1}', str(self.count+1))
        css = self.css.replace('{NUM_ROWS}', str(rows_per_col+added_extra_row)).replace('{NUM_COLS}', str(num_cols))
        display(HTML(html+css))
        self.frame_start = time.time()

    def update(self, bar_id, stage, progress, stage_complete=True):
        if bar_id in self.progressTracker and not self.isDone():
            self.progressTracker[bar_id] += progress
            if self.progressTracker[bar_id] > self.metrics_max:
                while self.progressTracker[bar_id] > self.metrics_max:
                    self.metrics_max *= 1.2
                self.render_buffer = ''
                self.update_scale = True
            else:
                self._update_bar(bar_id)

            now = time.time()
            if now - self.frame_start > self.frame_delay:
                self._refresh()
                self.frame_start = now

            if stage_complete:
                self._update_stages(stage)
                if stage+1 == self.end_stage:
                    self.complete(bar_id)
                if self.progressTracker[bar_id] > self.slowest_per_stage[stage]:
                    self.slowest_per_stage[stage] = self.progressTracker[bar_id]
                if self.stages[stage] == 0:
                    self._update_timestamp(stage, self.slowest_per_stage[stage])

    def _update_bar(self, bar_id):
        part = math.floor(self.progressTracker[bar_id] / self.metrics_max * 100 + 1)
        render = self.js_update_bar.replace('{ID}', str(bar_id)).replace('{PART}', str(part))
        self.render_buffer += render

    def _refresh(self):
        if self.update_scale:
            for bar_id in self.progressTracker.keys():
                self._update_bar(bar_id)
            self.update_scale = False
        display(Javascript(self.render_buffer))
        self.render_buffer = ''

    def _update_stages(self, stage):
        self.stages[stage] -= 1
        self.stages[stage+1] += 1

        render = self.js_update_stage.replace('{STAGE}', str(stage)).replace('{PART}', str(self.stages[stage]))
        render += self.js_update_stage.replace('{STAGE}', str(stage+1)).replace('{PART}', str(self.stages[stage+1]))
        display(Javascript(render))

    def _update_timestamp(self, stage, time):
        render = self.js_update_timestamp.replace('{STAGE}', str(stage)).replace('{TIME}', str(round(time, 2)))
        display(Javascript(render))

    def complete(self, bar_id):
        if bar_id in self.progressTracker and not self.isDone():
            self.count -= 1
            render = self.js_complete_bar.replace('{ID}', str(bar_id))
            display(Javascript(render))

    def isDone(self):
        return not self.count
