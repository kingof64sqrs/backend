module.exports = {
  apps: [
    {
      name: "aroundyou-api",
      script: "uv",
      args: "run uvicorn app.main:app --host 0.0.0.0 --port 3000",
      interpreter: "none",
      cwd: "/home/ubuntu/backend",
      env: {
        APP_ENV: "prod",
      },
      autorestart: true,
      max_restarts: 10,
      restart_delay: 1000,
      time: true,
    },
  ],
};
