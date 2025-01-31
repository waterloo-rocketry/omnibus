import D3LineChart from "../D3LineChart/D3LineChart";


interface D3TesterProps {
    numCharts: number
}

function D3Tester(props: D3TesterProps) {

    return (
        <div className="flex flex-row flex-wrap">
            {
                Array.from({ length: props.numCharts }).map((_, index) =>
                    <D3LineChart key={index} />
                )
            }
        </div>
    )
}

export default D3Tester;