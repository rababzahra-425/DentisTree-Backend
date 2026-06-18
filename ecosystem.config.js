module.exports = {
  apps: [
    {
      name: "dentistree-backend",
      cwd: "/opt/dentistree/DentisTree-Backend",

      // Run gunicorn through the venv's python so the correct interpreter
      // and installed packages are used.
      script: "./venv/bin/gunicorn",
      interpreter: "./venv/bin/python3",
      args: "project.wsgi:application --bind 127.0.0.1:8005 --workers 3",

      // Fork mode: PM2 supervises ONE process (the gunicorn master),
      // and gunicorn manages its own 3 workers. Do NOT use cluster mode.
      exec_mode: "fork",
      instances: 1,

      autorestart: true,
      max_restarts: 10,
      min_uptime: "10s",

      // Give gunicorn time to drain in-flight requests on stop/restart.
      kill_timeout: 5000,

      // MONGO_URI and other secrets are loaded by the app from project/.env
      // (via python-dotenv in app/models.py), so no env is set here.
      env: {},

      out_file: "/opt/dentistree/DentisTree-Backend/pm2-out.log",
      error_file: "/opt/dentistree/DentisTree-Backend/pm2-err.log",
      merge_logs: true,
      time: true,
    },
  ],
};
