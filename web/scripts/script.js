

let trace1 = {
    y: [0],
    type: 'line',
    line: {
        color: '#ffc669',
      }
};

let data = [trace1];

let layout = {
    showlegend: false,
    margin: {l:30, r:30, b:30, t:30},
    font:{color: '#f5f5f5'},
    paper_bgcolor: '#2b294b',
    plot_bgcolor: '#2b294b',
};
  
Plotly.newPlot('monitoring__chart', data, layout, {displayModeBar: false});

let count = 0;

const readTemp = () => {
    temp_element = document.getElementById("temperatura_actual");

    eel.getData()((ret) => {
        temperatura_actual = ret['temperatura_actual'];

        temp = Math.round(temperatura_actual * 10) / 10
        temp_element.textContent = temp;
        Plotly.extendTraces('monitoring__chart', { y:[ [temp] ] }, [0])
        count++;

        if (count > 20) {
            Plotly.relayout('monitoring__chart', {
                xaxis: {
                    range: [count-20, count]
                }
            });
        }
    })
}

setInterval(readTemp, 4000)