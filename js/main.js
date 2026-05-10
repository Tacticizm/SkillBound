const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
canvas.width = 800;
canvas.height = 600;

const world = new GameMap(32);
const player = new Entity(100, 100, 'blue');

function gameLoop() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    world.draw(ctx);
    player.update(InputHandler, world); // InputHandler from input.js
    player.draw(ctx);

    requestAnimationFrame(gameLoop);
}

gameLoop();