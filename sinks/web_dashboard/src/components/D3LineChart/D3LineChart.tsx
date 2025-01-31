import * as d3 from 'd3';
import { useEffect, useRef, useState } from 'react';


function D3Tester() {

    var lastUpdated = useRef(Date.now());
    const d3Container = useRef(null);

    const [data, setData] = useState([{
        x: 0,
        y: Math.floor(Math.random() * 500),
    }]);
    
    useEffect(() => {
        console.log("Data points per second: ", 1000 / (Date.now() - lastUpdated.current));
        lastUpdated.current = Date.now();
    }, [data])

    useEffect(() => {

        var i = 0;

        const interval = setInterval(() => {

            setData((prevData: { x: number, y: number }[]) => {
                prevData = [...prevData, {
                    x: i+1,
                    y: Math.floor(Math.random() * 3000)
                }];

                return prevData.length > 100 ? prevData.slice(1) : prevData;
            });

            i ++;

        }, 1);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {

        const width = 300, height = 200;
        const svg = d3.select(d3Container.current)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const xScale = d3.scaleLinear()
            .domain(d3.extent(data, d => d.x) as [number, number])
            .range([20, width - 20]);

        const yScale = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.y) as number])
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

        const line = d3.line<{ x: number; y: number }>()
            .x(d => xScale(d.x))
            .y(d => yScale(d.y));

        svg.append('path')
            .datum(data)
            .attr('fill', 'none')
            .attr('stroke', 'blue')
            .attr('stroke-width', 2)
            .attr('d', line);

        return () => { svg.remove() };
    }, [data]);

    return (
        <div className="text-amber-50" ref={d3Container} />
    );
}

export default D3Tester;