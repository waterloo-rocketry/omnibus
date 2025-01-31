import { useEffect, useState, useRef } from 'react';
import { XYChart, LineSeries, Axis, darkTheme } from '@visx/xychart';

interface VisxTesterProps {
    numCharts: number
}

function VisxLineChart(props: VisxTesterProps) {
    
    const lastUpdated = useRef(Date.now());

    const [data, setData] = useState([{ x: 0, y: Math.floor(Math.random() * 500) }]);

    useEffect(() => {
        console.log("Data points per second: ", 1000 / (Date.now() - lastUpdated.current));
        lastUpdated.current = Date.now();
    }, [data]);

    useEffect(() => {
        let i = 0;
        const interval = setInterval(() => {
            setData((prevData) => {
                const newData = [...prevData, { x: i + 1, y: Math.floor(Math.random() * 3000) }];
                return newData.length > 100 ? newData.slice(1) : newData;
            });
            i++;
        }, 1);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className='flex flex-row flex-wrap'>
            {Array.from({ length: props.numCharts }).map((_, index) => 
                <XYChart 
                    key={index}
                    height={300}
                    width={300}
                    xScale={{ type: 'linear', zero: false }}
                    yScale={{ type: 'linear' }}
                    theme={darkTheme}
                >
                    <LineSeries
                        dataKey="Live Data"
                        data={data}
                        xAccessor={(d) => d.x}
                        yAccessor={(d) => d.y}
                    />
                    <Axis orientation="bottom" />
                    <Axis orientation="left" />
                </XYChart>
            )}
        </div>
    );
}

export default VisxLineChart;
