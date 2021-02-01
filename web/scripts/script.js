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



const iniciar_proceso = () => {
    console.log("1");
    let lower = document.getElementById("input-limite-inferior").value;
    let upper = document.getElementById("input-limite-superior").value;
    let gradient = document.getElementById("input-gradiente").value;
    console.log("2");
    let message;

    if (lower != "" && upper != "" && gradient != "") {
        lower = parseFloat(lower)
        upper = parseFloat(upper)
        gradient = parseFloat(gradient)
        console.log("2");
        eel.iniciar(lower, upper, gradient)((ret) => {
            console.log("3");
            message = ret['message']
            document.getElementById("mensaje").textContent = message;
        })

    } else {
        message = "Todos los campos son requeridos"
        document.getElementById("mensaje").textContent = message;
    }
}

const terminar_proceso = () => {
    eel.terminar()((ret) => {
        let message = ret['message']
        document.getElementById("mensaje").textContent = message;
    })
}

boton_iniciar_proceso = document.getElementById("start")
boton_iniciar_proceso.addEventListener('click', iniciar_proceso)

boton_terminar_proceso = document.getElementById("end")
boton_terminar_proceso.addEventListener('click', terminar_proceso)