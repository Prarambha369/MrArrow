_G.love = require("love")

local screen = {
    w = love.graphics.getWidth(),
    h = love.graphics.getHeight()
}

function love.load()
    target = love.graphics.newImage("assets/images/target.png")
 
    image_width = target:getWidth()
    image_height = target:getHeight()

    target = {}
    math.randomseed(os.time())
    target.x = math.random(100, 900)
    target.y = math.random(50,100)

    target.x1 = math.random(100, 900)
    target.y = math.random(50,100)

    player = {}
    player.x = 0
    player.y = 690
end
function love.update(dt)


end
function love.draw( ... )
    -- love.graphics.draw(target, screen.w / 2, screen.h / 2, nil,10,10, image_width / 2, image_height / 2)
    love.graphics.setColor(1, 0, 0)
    love.graphics.circle("fill", target.x,target.y,26, 100)
    love.graphics.circle("fill", target.x,target.y,26, 100)
    love.graphics.circle("fill", target.x,target.y,26, 100)

    love.graphics.setColor(1,0,0)
    love.graphics.rectangle("fill",player.x,player.y,42,42)
end