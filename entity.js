class Entity {
    constructor(x, y, color) {
        this.x = x;
        this.y = y;
        this.speed = 4;
        this.color = color;
    }

    update(input, map) {
        // Logic for movement and collision detection goes here
    }

    draw(ctx) {
        ctx.fillStyle = this.color;
        ctx.fillRect(this.x, this.y, 32, 32);
    }
}
