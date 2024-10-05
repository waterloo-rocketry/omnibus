<script lang="ts">
    import { onDestroy, onMount } from 'svelte'
    let cheese = 0
    let timer = 0
    let timerService: number
    onMount(() => (timerService = setInterval(increaseTimer, 1000)))
    onDestroy(() => clearInterval(timerService))
    function increaseTimer(): void {
        timer = timer + 1
    }

    $: hrs = Math.floor(timer / 3600)
    $: mins = Math.floor((timer - hrs * 3600) / 60)
    $: secs = Math.floor(timer - hrs * 3600 - mins * 60)

    function padNumber(num: number) {
        if (num === 0) return '00'
        if (num < 10) return '0' + num.toString()
        return num.toString()
    }
</script>

<main class="grid grid-cols-1 grid-rows-1 h-screen text-white bg-neutral-900">
    <div class="flex flex-col gap-4 m-8">
        <div class="flex flex-row align-middle">
            <div class="text-4xl flex-1">
                <a href="https://waterloorocketry.com">
                    <img class=" h-12" src="./banner_logo.png" alt="Waterloo Rocketry" srcset="" />
                </a>
            </div>
            <h2 class="text-xl text-right">Launch Dashboard</h2>
        </div>
        <!-- This would obviously be replaced with a local alternative -->
        <div class="flex-grow flex flex-col justify-center">
            <iframe
                src="https://www.openstreetmap.org/export/embed.html?bbox=-80.64514160156251%2C43.42650077305852%2C-80.50300598144533%2C43.516694729135544&amp;layer=mapnik"
                style="border: 1px solid black; width: 100%; height: 100%"
                title="OpenStreetMap Map"
            ></iframe>
        </div>
        <div class="grid grid-cols-4 gap-8">
            <!-- Fix the centering method later for mobile support -->
            <div class=" flex flex-col-reverse">
                <div>Velocity: 400km/h</div>
                <div>Acceleration: something</div>
                <div>Distance from Ground: Something</div>
            </div>
            <div class=" col-span-2 flex flex-col-reverse text-center gap-3">
                <div class=" text-8xl">T+{padNumber(hrs)}:{padNumber(mins)}:{padNumber(secs)}</div>
                <div class="text-xl">Launch State: Payload Released</div>
            </div>
            <div class=" outline-2 outline-white outline">
                Rocket Log Messages (or team camera feed):
                <br />
                <button
                    class="p-2 m-2 bg-yellow-500 text-black outline outline-2 rounded-lg hover:bg-yellow-100"
                    on:click={() => {
                        cheese++
                    }}>Cheese: {cheese}</button
                >
            </div>
        </div>
    </div>
</main>
