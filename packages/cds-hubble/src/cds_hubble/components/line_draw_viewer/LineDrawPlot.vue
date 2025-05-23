<script>
export default {
  name: "LineDrawPlot",
  props: ["chart_id", "draw_active", "fit_active", "line_drawn", "line_fit", "plot_data", "x_axis_label", "y_axis_label", "height", "margins", "display_best_fit_gal", "best_fit_gal_layer_index", "clear_class_layer", "clear_drawn_line", "clear_fit_line", "bfg_color"],
  async mounted() {
    await window.plotlyPromise;

    let xmin = 0;
    let xmax = 0;
    let ymin = 0;
    let ymax = 0;
    this.plot_data?.forEach(trace => {
      // NB: We can't call e.g. Math.min.apply because of the observer object that Vue puts into the array
      xmin = Math.min(xmin, Math.min(...trace.x));
      ymin = Math.min(ymin, Math.min(...trace.y));
      xmax = Math.max(xmax, Math.max(...trace.x));
      ymax = Math.max(ymax, Math.max(...trace.y));
    });
    if (this.plot_data?.length > 0) {
      for (const layer of this.plot_data) {
        this.chart.traces.push(this.fitLineData(layer.marker.color));
      }
    }
    const layout = this.chart.layout;
    layout.xaxis.range = [0, xmax*1.1];
    layout.yaxis.range = [0, ymax*1.1];
    layout.xaxis.title = { text: this.x_axis_label };
    layout.yaxis.title = { text: this.y_axis_label };
    layout.height = this.height;
    layout.margin = this.margins;

    Plotly.newPlot(this.$refs[this.chart_id], this.chart.traces, layout, this.chart.config)
      .then(() => {
        this.element = document.getElementById(this.chart_id);
        this.dragLayer = this.element.querySelector(".nsewdrag");
        const count = this.plot_data?.length ?? 0;
        if (this.plot_data) {
          this.plotDataCount = count;
          Plotly.addTraces(this.chart_id, this.plot_data);
        }
        this.fitLineTraceIndices = Array.from({length: count}, (x, i) => i + 1);
        this.setupMouseHandlers(this.draw_active);
        this.setupPlotlyHandlers(this.draw_active);
        this.setupPlotlyRestyleHandler();
      });

  },
  data() {
    const baseAxis = {
      showspikes: false,
      zeroline: false,
      mirror: true,
      ticks: "outside",
      showline: true,
      showgrid: false,
      showticklabels: true,
      autorange: false,
      automargin: true,
    };

    const xaxis = { ...baseAxis, range: [0, 1] };
    const yaxis = { ...baseAxis, range: [0, 1] };
    return {
      chart: {
        uuid: this.chart_id,
        traces: [
          {
            x: [0, 0],
            y: [0, 0],
            line: {
              color: "#000000",
              width: 4,
              shape: "line"
            },
            visible: false,
            hoverinfo: "skip",
            showlegend: false,
          },

        ],
        layout: {
          xaxis,
          yaxis,
          hovermode: "none",
          dragmode: false,
          showlegend: true,
          legend: {
            xanchor: "left",
            yanchor: "top",
            x: 0.01,
            y: 0.99,
          }
        },
        config: { displayModeBar: false, responsive: true },
      },
      element: null,
      lineDrawn: false,
      mouseDown: false,
      movingLine: false,
      lastEndpoint: null,
      hoveringEndpoint: false,
      plotDataCount: 0,
      drawnLineTraceIndex: 0,
      fitLineTraceIndices: [],
      endpointSize: 10,
      lastFitSlopes: [],
      endpointTraceIndex: 0,
      bestFitGalaxyTraceIndex: 0,
      range: 0,
    };
  },
  methods: {
    fitLineData(color="#000000") {
      return {
        x: [0, 0],
        y: [0, 0],
        line: {
          color,
          width: 4,
          shape: "line"
        },
        visible: false,
        hoverinfo: "skip",
        showlegend: this.line_label != null,
      };
    },
    screenToWorld(event) {
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const xWorld = layout.xaxis.p2c(x - layout.margin.l);
      const yWorld = layout.yaxis.p2c(y - layout.margin.t);
      return [xWorld, yWorld];
    },
    worldToScreen(worldX, worldY) {
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const xScreen = layout.xaxis.c2p(worldX) + layout.margin.l + rect.left;
      const yScreen = layout.yaxis.c2p(worldY) + layout.margin.t + rect.top;
      return [xScreen, yScreen];
    },
    updateLine(event) {
      const [xWorld, yWorld] = this.screenToWorld(event);
      Plotly.update(
        this.chart_id,
        { 'x.1': xWorld, 'y.1': yWorld },
        {},
        [this.drawnLineTraceIndex]
      );
    },
    mouseMoveHandler(event) {
      if (this.movingLine) {
        this.updateLine(event);
      }
    },
    mouseDownHandler(event) {
      this.mouseDown = true;
    },
    mouseUpHandler(event) {
      this.mouseDown = false;
      if (this.movingLine) {
        this.movingLine = false;
        this.drawEndpoint(event);
        this.lineDrawn = true;
        const cursor = this.overEndpoint(event) ? "grab" : "default";
        this.setCursor(cursor);
        if (this.line_drawn) {
          this.line_drawn();
        }
      }
    },
    plotlyClickHandler(event) {
      console.log("endpointTraceIndex", this.endpointTraceIndex);
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.movingLine = true;
        this.clearEndpoint();
      }
    },
    plotlyHoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        this.setCursor("grab");
      }
    },
    plotlyUnhoverHandler(event) {
      if (event.points[0].curveNumber === this.endpointTraceIndex) {
        let cursor;
        if (this.movingLine) {
          cursor = this.lineDrawn ? "grabbing" : "default";
        } else {
          cursor = "crosshair";
        }
        this.setCursor(cursor);
      }
    },
    setCursor(type) {
      this.element.style.cursor = type;
      this.dragLayer.style.cursor = type;
      // This class sets the cursor to be the crosshair on Plotly
      // so we need a bit of special handling here
      if (type === "crosshair") {
        this.dragLayer.classList.add("cursor-crosshair");
      } else {
        this.dragLayer.classList.remove("cursor-crosshair");
      }
    },
    setDrawnLineVisibility(visible) {
      Plotly.update(this.chart_id, { visible }, {}, [this.drawnLineTraceIndex]);
    },
    clearEndpoint() {
      const dataTracesCount = this.plot_data?.length ?? 0;
      if (this.element.data.length > dataTracesCount + 1) {
        try {
          console.log("clearing endpointTraceIndex", this.endpointTraceIndex);
          Plotly.update(this.chart_id, { visible: false }, {}, [this.endpointTraceIndex]);
        } catch (e) {
          console.warn(e);
        }
      }
      this.lastEndpoint = null;
    },
    overEndpoint(event) {
      if (this.lastEndpoint === null) {
        return false;
      }
      const layout = this.element._fullLayout;
      const rect = this.element.getBoundingClientRect();
      const x = event.clientX;
      const y = event.clientY;
      const endpointScreen = this.worldToScreen(...this.lastEndpoint);
      const relX = x - endpointScreen[0];
      const relY = y - endpointScreen[1];
      return Math.pow(relX, 2) + Math.pow(relY, 2) <= Math.pow(this.endpointSize / 2, 2);
    },
    drawEndpoint(event) {
      // If the mouse is moving quickly, it's possible for the endpoint to be
      // a bit off from the line if we just use the screen coordinates of the event.
      // So instead, just draw the endpoint at the end of the line
      const line = this.element.data[this.drawnLineTraceIndex];
      const x = line.x[1];
      const y = line.y[1];
      Plotly.addTraces(this.chart_id, { x: [x], y: [y], type: "scatter", mode: "markers", marker: { size: this.endpointSize, color: "#000000" }, hoverinfo: "none", showlegend: false });
      this.lastEndpoint = [x, y];
      // Try storing actual endpoint trace index
      const chartElement = document.getElementById(this.chart_id);
      if (chartElement) {
        const nTraces = chartElement.data.length;
        this.endpointTraceIndex = nTraces - 1;
        console.log("endpointTraceIndex", this.endpointTraceIndex)
      }
    },
    linearRegression(x, y, forceOrigin=true) {
      const sum = (s, a) => s + a;
      const sumXY = x.reduce((s, a, i) => s + a * y[i], 0);
      const sumXsq = x.reduce((s, a) => s + a * a, 0);
      if (forceOrigin) {
        const a = sumXY / sumXsq;
        return [a, 0];
      } else {
        const n = x.length;
        const sumX = x.reduce(sum);
        const sumY = y.reduce(sum);
        const xAvg = sumX / n;
        const yAvg = sumY / n;
        const a = (n * sumXY - (sumX * sumY)) / (n * sumXsq - (sumX * sumX));
        const b = yAvg - a * xAvg;
        return [a, b];
      }
    },
    fitLineResults(x, y) {
      const [a, b] = this.linearRegression(x, y);
      const xs = this.element._fullLayout.xaxis.range;
      const ys = xs.map(v => a * v + b);
      return [[a, b], [xs, ys]];
    },
    onPlotlyRestyle(event) {
      const visibilityUpdate = "visible" in event[0];
      if (!(this.fit_active && visibilityUpdate)) {
        return;
      }
      const relevantIndices = this.fitLineTraceIndices.filter(idx => event[1].includes(idx + this.plotDataCount));
      const visible = event[0]["visible"];
      Plotly.update(this.chart_id, { visible }, {}, relevantIndices);
    },
    setupMouseHandlers(draw_active) {
      // Using document as the event listener for mouseup is intentional
      // See this thread here: https://community.plotly.com/t/plotly-onmousedown-and-onmouseup/4812
      // For some reason, mousedown works fine on the Plotly graph, but not mouseup
      // Any ideas on how to not need to do this would be great!
      if (draw_active) {
        this.element.addEventListener("mousemove", this.mouseMoveHandler);
        this.element.addEventListener("mousedown", this.mouseDownHandler);
        document.addEventListener("mouseup", this.mouseUpHandler);
      } else if (this.element != null) {
        this.element.removeEventListener("mousemove", this.mouseMoveHandler);
        this.element.removeEventListener("mousedown", this.mouseDownHandler);
        document.removeEventListener("mouseup", this.mouseUpHandler);
      }
    },
    setupPlotlyHandlers(draw_active) {
      this.element.on("plotly_legendclick", (data) => false);
      this.element.on("plotly_legenddoubleclick", (data) => false);
      if (draw_active) {
        this.element.on("plotly_click", this.plotlyClickHandler);
        this.element.on("plotly_hover", this.plotlyHoverHandler);
        this.element.on("plotly_unhover", this.plotlyUnhoverHandler);
      } else {
        this.element.removeListener("plotly_click", this.plotlyClickHandler);
        this.element.removeListener("plotly_hover", this.plotlyHoverHandler);
        this.element.removeListener("plotly_unhover", this.plotlyUnhoverHandler);
      }
    },
    setupPlotlyRestyleHandler() {
      this.element.on("plotly_restyle", this.onPlotlyRestyle);
    },

  },
  watch: {
    chart() {
      Plotly.react(
        this.$refs["chart"],
        this.chart.traces,
        this.chart.layout
      );
    },
    draw_active(value) {
      this.movingLine = value && this.lastEndpoint === null;
      console.log(value, this.lastEndpoint, this.movingLine);
      console.log("making visible trace index", this.drawnLineTraceIndex);
      if (value) {
        this.setDrawnLineVisibility(true);
      }
      this.setupMouseHandlers(value);
      this.setupPlotlyHandlers(value);
    },
    fit_active(value) {
      if (value && this.plotDataCount > 0) {
        const slopes = [];
        for (const [index, layer] of this.plot_data.entries()) {
          const x = layer.x;
          const y = layer.y;
          const [[a, _], [xs, ys]] = this.fitLineResults(x, y);
          let update = {
            visible: value && (this.element.data[index + 1 + this.plotDataCount].visible ?? true),
            'x.0': xs[0],
            'x.1': xs[1],
            'y.0': ys[0],
            'y.1': ys[1],
          };
          Plotly.update(this.chart_id, update, {}, [index + 1]);
          slopes.push(a);
        }
        this.lastFitSlopes = slopes;
        this.range = this.element._fullLayout.xaxis.range[1] - this.element._fullLayout.xaxis.range[0];     
        if (this.line_fit) {
          this.line_fit({slopes, range: this.range});
        }
      } else {
        console.log("clearing fit line traces", this.fitLineTraceIndices);
        Plotly.update(this.chart_id, { visible: false }, {}, this.fitLineTraceIndices);
      }
    },
    display_best_fit_gal(value) {
      if (value) {
        if (this.fit_active) {
          x_best_fit_galaxy = 0.5 * this.range;
          const slopes = this.lastFitSlopes;
          if (slopes.length > 0) {
            const bestfitslope = slopes[this.best_fit_gal_layer_index];
            y_best_fit_galaxy = bestfitslope * x_best_fit_galaxy;
            const trace = {
              x: [Math.round(x_best_fit_galaxy)],
              y: [Math.round(y_best_fit_galaxy)],
              mode: "markers", 
              marker: { size: 14, color: this.bfg_color },
              visible: true,
              hoverinfo: "skip",
              showlegend: false,
            };
            Plotly.addTraces(this.chart_id, trace);
            // Store best fit galaxy trace index
            if (this.element) {
              const nTraces = this.element.data.length;
              this.bestFitGalaxyTraceIndex = nTraces - 1;
            }
          }
        } else {
          // If fit is not active, no best fit galaxy to display
          return;
        }
      } else if (this.bestFitGalaxyTraceIndex > 0) {
        try {
          console.log("clearing best fit galaxy trace", this.bestFitGalaxyTraceIndex);
          Plotly.update(this.chart_id, { visible: false }, {}, [this.bestFitGalaxyTraceIndex]);
        } catch (e) {
          console.warn(e);
        }
      }
    },
    clear_drawn_line(value) {
      try {
        console.log("clearing drawn line, index", this.drawnLineTraceIndex);
        this.clearEndpoint();
        this.setDrawnLineVisibility(false);
      } catch (e) {
        console.warn(e);
      } 
    },
    clear_class_layer(value) {
      try {
        console.log("clearing class layer, index", this.plotDataCount + 1);
        Plotly.update(this.chart_id, { visible: false }, {}, [this.plotDataCount + 1]);
      } catch (e) {
        console.warn(e);
      }        
    },
    line_label(value) {
      const indices = this.fitLineTraceIndices.filter(idx => this.element.data[idx].visible);
      Plotly.update(this.chart_id, { showlegend: value != null && value.length > 0, name: value }, {}, indices);
    },
    movingLine(value) {
      if (value) {
        const cursor = this.lineDrawn ? "grabbing" : "default";
        this.setCursor(cursor);
      }
    }
  }
}
</script>

<template>
<div
  :ref="chart_id"
  :id="chart_id"
></div>
</template>

<style>
.svg-container {
  width: 100% !important;
}

.main-svg {
  width: 100% !important;
  border-bottom-left-radius: 5px;
  border-bottom-right-radius: 5px;
}
</style>
