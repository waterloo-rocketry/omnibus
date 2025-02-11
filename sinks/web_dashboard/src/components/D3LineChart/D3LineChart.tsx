import * as d3 from 'd3';
import { useEffect, useRef, useState } from 'react';

interface DataProps {
    data: number[][]
}

function D3LineChart ( {data}: DataProps) {

    var lastUpdated = useRef(Date.now());
    const d3Container = useRef(null);

    let index = useRef(0);
    let total = useRef(0);
    let tick = useRef(Date.now());

    useEffect(() => {

        if (index.current < 10) {
            total.current ++; 
        } else {
            console.log("Data points per second: ", total.current / ((Date.now()-tick.current)/1000));

            tick.current = Date.now();
            total.current = 0;
            index.current = 0;
        }

        index.current ++;
        lastUpdated.current = Date.now();
    }, [data])

    useEffect(() => {

        const width = 300, height = 200;
        const svg = d3.select(d3Container.current)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const xScale = d3.scaleLinear()
            .domain(d3.extent(data, d => d[0]) as [number, number])
            .range([20, width - 20]);

        const yScale = d3.scaleLinear()
            .domain([0, d3.max(data, d => d[1]) as number])
            .range([height - 20, 20]);

        const xAxis = d3.axisBottom(xScale);
        svg.append('g')
            .attr('transform', `translate(0, ${height - 20})`)
            .call(xAxis);

        svg.append('text')
            .attr('x', width / 2)
            .attr('y', height - 5)
            .attr('text-anchor', 'middle')
            .text('X Axis');

        const yAxis = d3.axisLeft(yScale);
        svg.append('g')
            .attr('transform', 'translate(20, 0)')
            .call(yAxis);

        svg.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('x', -height / 2)
            .attr('y', 15)
            .attr('text-anchor', 'middle')
            .text('Y Axis');

        const line = d3.line<number[]>()
            .x(d => xScale(d[0]))
            .y(d => yScale(d[1]));

        svg.append('path')
            .datum(data)
            .attr('fill', 'none')
            .attr('stroke', 'blue')
            .attr('stroke-width', 2)
            .attr('d', line);

        return () => {
            svg.remove();
        };
    }, [data]);

    return (
        <div className="text-amber-50" ref={d3Container} />
    );
}

export default D3LineChart;