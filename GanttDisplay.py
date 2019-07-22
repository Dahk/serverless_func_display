from IPython.display import display, HTML, Javascript
import math

class GanttDisplay():
    def __init__(self, idlist):
        self.progressTracker = {
            bar_id : {
                'stage': 0,
                'chrono': [0, 0, 0]
            }
            for bar_id in idlist
        }
        self.count = len(idlist)
        self.stages = [self.count, 0, 0, 0]
        self.end_stage = len(self.stages)-1
        self.slowest_per_stage = [0, 0, 0]
        self.metrics_max = 10
        self.css = """
        <style>
        .gantt {
            display: grid;
            grid-template-rows: repeat({NUM_WORKERS}, 30px) 2px 3px 30px;
            background-color: #EEE;
            border: 0;
            border-radius: 12px;
            position: relative;
            overflow: hidden;
            box-sizing: border-box;
            box-shadow: 0 75px 125px -57px #7e8f94;
        }
        .gantt-row {
            display: grid;
            grid-template-columns: 125px 2px 1fr;
            height: 30px;
        }
        .gantt-row:nth-child(even) {
            background-color: #d3d3d3;
        }
        .gantt-row-label {
            grid-column: 1;
            padding: 5px;
            font-weight: bold;
            text-align: center;
        }
        .gantt-row-bars {
            list-style: none;
            display: grid;
            grid-template-columns: repeat(1000, 1fr);
            grid-template-rows: auto;
            grid-column: 3;
            padding: 1px 0;
            font-weight: 500;
            text-align: center;
            font-size: 14px;
            overflow: hidden;
            position: relative;
            column-gap: 0px;
        }
        .gantt-row-bars div:nth-of-type(1) {
            background-color: #034561;
            padding-top: 4px;
            color: #fff;
            border-radius: 14px;
        }
        .gantt-row-bars div:nth-of-type(2) {
            background-color: #409d9b;
            padding-top: 4px;
            color: #fff;
            border-radius: 14px;
        }
        .gantt-row-bars div:nth-of-type(3) {
            background-color: #4fb783;
            padding-top: 4px;
            color: #fff;
            border-radius: 14px;
        }
        .gantt-row-pins {
            display: grid;
            grid-template-columns: repeat(1000, 1fr);
            grid-template-rows: 5px;
            grid-column: 3;
            grid-column-gap: 0px;
            position: relative;
            margin: 0px;
            column-gap: 0px;
        }
        .gantt-row-pins div {
            background-color: #333;
        }
        .vsep {
            background-color: #333;    
            grid-column: 2;
        }
        .hsep {
            background-color: #333;
            grid-row: {HSEP_ROW};
        }
        .tooltip-metrics {
        }
        .tooltip-metrics .tooltiptext-metrics {
            visibility: hidden;
            top: -5px;
            right: 105%; 
            width: 80px;
            background-color: black;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px 0;
            position: absolute;
            z-index: 1;
        }
        .tooltip-metrics:hover .tooltiptext-metrics {
            visibility: visible;
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
        <div class="gantt-row" style="grid-row: {ROW};">
            <div id="bar{ID}-label" class="gantt-row-label"> worker #{ID} </div>
            <div class="vsep"></div>
            <div class="gantt-row-bars">
                <div id="bar{ID}-stage0" style="grid-column: 1; display: none;">Fetch</div>
                <div id="bar{ID}-stage1" style="grid-column: 999; display: none;">Process</div>
                <div id="bar{ID}-stage2" style="grid-column: 1000; display: none;">Upload</div>
            </div>
        </div>
        """
        self.html_template = """
        <meta charset="UTF-8">
        <div style="background-color: #cddade; padding: 30px; position: relative;">
        <div class="gantt">
            {ROWS}
            <div class="hsep"></div>
            <div class="gantt-row" style="grid-row: {PINS_ROW}; background-color: #eee">
                <div></div>
                <div></div>
                <div class="gantt-row-pins">
                    <div style="grid-column: 50/52;"></div>
                    <div style="grid-column: 100/102;"></div>
                    <div style="grid-column: 150/152;"></div>
                    <div style="grid-column: 200/202;"></div>
                    <div style="grid-column: 250/252;"></div>
                    <div style="grid-column: 300/302;"></div>
                    <div style="grid-column: 350/352;"></div>
                    <div style="grid-column: 400/402;"></div>
                    <div style="grid-column: 450/452;"></div>
                    <div style="grid-column: 500/502;"></div>
                    <div style="grid-column: 550/552;"></div>
                    <div style="grid-column: 600/602;"></div>   
                    <div style="grid-column: 650/652;"></div>
                    <div style="grid-column: 700/702;"></div>
                    <div style="grid-column: 750/752;"></div>
                    <div style="grid-column: 800/802;"></div>
                    <div style="grid-column: 850/852;"></div>
                    <div style="grid-column: 900/902;"></div>
                    <div style="grid-column: 950/952;"></div>
                    <div style="grid-column: 999/1001;"></div>
                </div>
            </div>
            <div class="gantt-row" style="grid-row: {METRICS_ROW}; background-color: #eee">
                <div></div>
                <div></div>
                <div id="metrics" style="grid-column: 3; position: relative; margin-left: 8px; grid-template-columns: repeat(100, 1fr);">
                    <span style="position: absolute; left: 8%;">1</span>
                    <span style="position: absolute; left: 18%;">2</span>
                    <span style="position: absolute; left: 28%;">3</span>
                    <span style="position: absolute; left: 38%;">4</span>
                    <span style="position: absolute; left: 48%;">5</span>
                    <span style="position: absolute; left: 58%;">6</span>     
                    <span style="position: absolute; left: 68%;">7</span>
                    <span style="position: absolute; left: 78%;">8</span>
                    <span style="position: absolute; left: 88%;">9</span>
                    <span class="tooltip-metrics" style="position: absolute; left: 98%;">10</span>
                </div>
            </div>
            <div class="gantt-row" style="grid-row: {UNITS_DESC_ROW}; background-color: #eee">
                <div></div>
                <div></div>
                <div style="grid-column: 3; position: relative;">
                    <span style="position: absolute; left: 40%;">wallclock time (sec)</span>
                </div>
            </div>
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

        var elem = document.getElementById("bar{ID}-stage{STAGE}")
        elem.style.gridColumn = "{FROMTO}"
        elem.style.display = "block"
        """
        self.js_update_metrics = """
        var elems = document.getElementById("metrics").children
        var new_max = {NEW_MAX}
        for (var i=0; i<elems.length; i++){
            elems[i].innerHTML = (new_max / 10 * (i+1)).toFixed(2)
        }
        var desc = document.createElement("SPAN")
        desc.className = "tooltiptext-metrics"
        desc.innerHTML = elems[i-1].innerHTML
        elems[i-1].appendChild(desc)
        """
        self.js_complete_bar = """
        var elem = document.getElementById("bar{ID}-label")
        elem.innerHTML = "✔️" + elem.innerHTML
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
        rows = ''
        i = 1
        for bar_id in self.progressTracker.keys():
            rows = rows + self.html_row_template.replace('{ROW}', str(i)).replace('{ID}', str(bar_id))
            i += 1
        
        html = self.html_template.replace('{ROWS}', rows).replace('{PINS_ROW}', str(i+1))\
               .replace('{METRICS_ROW}', str(i+2)).replace('{UNITS_DESC_ROW}', str(i+3))\
               .replace('{NUM_WORKERS_PLUS1}', str(i)).replace('{NUM_WORKERS}', str(i-1))
        css = self.css.replace('{NUM_WORKERS}', str(i-1)).replace('{HSEP_ROW}', str(i))
        display(HTML(html+css))

    def update(self, bar_id, stage, progress, stage_complete=True):
        if bar_id in self.progressTracker and not self.isDone():
            bar = self.progressTracker[bar_id]
            if stage == bar['stage']:
                bar['chrono'][stage] += round(progress, 2)
            elif stage > bar['stage']:
                bar['chrono'][stage] = bar['chrono'][bar['stage']] + round(progress, 2)
                bar['stage'] = stage
            else:
                return

            max_end = bar['chrono'][stage]
            if max_end > self.metrics_max:
                #print('Doing max')
                self._update_max(max_end)
            else:
                #print('Doing single bar')
                self._update_bar(bar_id, bar)

            if stage_complete:
                self._update_stages(stage)
                if stage+1 == self.end_stage:
                    self.complete(bar_id)
                if bar['chrono'][stage] > self.slowest_per_stage[stage]:
                    self.slowest_per_stage[stage] = bar['chrono'][stage]
                if self.stages[stage] == 0:
                    self._update_timestamp(stage, self.slowest_per_stage[stage])

    def _update_bar(self, bar_id, bar):
        stage = bar['stage']
        #print(bar_id, ': ', bar['chrono'])
        if stage == 0:
            fromto = '1/{}'.format(math.floor(bar['chrono'][stage] / self.metrics_max * 1000) + 1)
        else:
            fromto = '{}/{}'.format(math.floor(bar['chrono'][stage-1] / self.metrics_max * 1000) + 1,
                                    math.floor(bar['chrono'][stage] / self.metrics_max * 1000) + 1)

        render = self.js_update_bar.replace('{ID}', str(bar_id)).replace('{STAGE}', str(stage)).replace('{FROMTO}', fromto)
        display(Javascript(render))

    def _update_max(self, surpassed_max):
        while surpassed_max > self.metrics_max:
            self.metrics_max = math.floor(self.metrics_max*1.5)

        render = ''
        iter_ids = iter(self.progressTracker.keys())
        for bar in self.progressTracker.values():
            if bar['chrono'][0] > 1:
                js_string = self.js_update_bar.replace('{ID}', str(next(iter_ids)))
                #print(bar['chrono'])
                last_end = math.floor(bar['chrono'][0] / self.metrics_max * 1000) + 1
                fromto = '1/{}'.format(last_end)
                render += js_string.replace('{STAGE}', '0').replace('{FROMTO}', fromto)

                for stage in range(1, bar['stage']+1):
                    next_end = math.floor(bar['chrono'][stage] / self.metrics_max * 1000) + 1
                    fromto = '{}/{}'.format(last_end, next_end)
                    render += js_string.replace('{STAGE}', str(stage)).replace('{FROMTO}', fromto)
                    last_end = next_end
        display(Javascript(render))
        self._update_metrics()

    def _update_metrics(self):
        render = self.js_update_metrics.replace('{NEW_MAX}', str(self.metrics_max))
        display(Javascript(render))

    def _update_stages(self, stage):
        self.stages[stage] -= 1
        self.stages[stage+1] += 1

        render = self.js_update_stage.replace("{STAGE}", str(stage)).replace('{PART}', str(self.stages[stage]))
        render += self.js_update_stage.replace("{STAGE}", str(stage+1)).replace('{PART}', str(self.stages[stage+1]))
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
