"""
apps/app_physics/services.py
=============================
Physics service for computing projectile trajectories with air drag.
"""

import math
import numpy as np


class ProjectileMotionService:
    """
    Computes trajectory of a sphere launched under gravity with quadratic air drag.
    Equations of motion solved numerically:
        m * a = m * g - 0.5 * C_d * rho * A * |v| * v
    """

    def __init__(
        self,
        velocity_m_s: float,
        angle_deg: float,
        mass_kg: float,
        diameter_m: float,
        drag_coefficient: float,
        gravity_m_s2: float = 9.80665,
        air_density_kg_m3: float = 1.225,
    ):
        self.v0 = velocity_m_s
        self.theta_rad = math.radians(angle_deg)
        self.m = mass_kg
        self.d = diameter_m
        self.Cd = drag_coefficient
        self.g = gravity_m_s2
        self.rho = air_density_kg_m3
        self.A = math.pi * (diameter_m / 2.0) ** 2

    def compute(self):
        # 1. Vacuum case (Analytic solution)
        t_flight_vac = (2.0 * self.v0 * math.sin(self.theta_rad)) / self.g
        t_flight_vac = max(t_flight_vac, 0.001)
        h_max_vac = (self.v0 * math.sin(self.theta_rad)) ** 2 / (2.0 * self.g)
        range_vac = self.v0 * math.cos(self.theta_rad) * t_flight_vac

        # Generate vacuum trajectory points
        t_pts_vac = np.linspace(0, t_flight_vac, 100)
        x_vac = self.v0 * math.cos(self.theta_rad) * t_pts_vac
        y_vac = self.v0 * math.sin(self.theta_rad) * t_pts_vac - 0.5 * self.g * t_pts_vac**2
        y_vac = np.clip(y_vac, 0, None)  # Ensure no sub-ground coordinates

        # 2. Drag case (Numerical integration using RK4 method)
        # State vector: [x, y, vx, vy]
        state = np.array([0.0, 0.0, self.v0 * math.cos(self.theta_rad), self.v0 * math.sin(self.theta_rad)])
        
        # RK4 ODE derivative function
        def derivatives(s):
            # s = [x, y, vx, vy]
            vx, vy = s[2], s[3]
            v = math.sqrt(vx**2 + vy**2)
            if v == 0:
                ax = 0.0
                ay = -self.g
            else:
                # Drag force = - 0.5 * Cd * rho * A * v * vec(v)
                drag_force_x = -0.5 * self.Cd * self.rho * self.A * v * vx
                drag_force_y = -0.5 * self.Cd * self.rho * self.A * v * vy
                ax = drag_force_x / self.m
                ay = -self.g + (drag_force_y / self.m)
            return np.array([vx, vy, ax, ay])

        dt = 0.01  # time step in seconds
        trajectory = [state.copy()]
        t = 0.0
        max_steps = 10000

        while state[1] >= 0.0 and len(trajectory) < max_steps:
            # RK4 Integration step
            k1 = derivatives(state)
            k2 = derivatives(state + k1 * (dt / 2.0))
            k3 = derivatives(state + k2 * (dt / 2.0))
            k4 = derivatives(state + k3 * dt)
            
            state += (k1 + 2.0 * k2 + 2.0 * k3 + k4) * (dt / 6.0)
            trajectory.append(state.copy())
            t += dt

            # Safeguard: stop if moving away/underground
            if len(trajectory) > 2 and state[1] < 0.0:
                break

        traj_arr = np.array(trajectory)
        
        # Interpolate final hit point for precision
        if len(traj_arr) > 1 and traj_arr[-1, 1] < 0.0:
            last = traj_arr[-2]
            current = traj_arr[-1]
            # fraction of step to hit ground y = 0
            fraction = -last[1] / (current[1] - last[1]) if current[1] != last[1] else 0.0
            hit_state = last + fraction * (current - last)
            traj_arr[-1] = hit_state
            t = t - dt + fraction * dt

        x_drag = traj_arr[:, 0]
        y_drag = traj_arr[:, 1]
        
        # Cap arrays at ~100 elements for client rendering efficiency
        step_sz = max(1, len(x_drag) // 100)
        x_drag_resampled = x_drag[::step_sz].tolist()
        y_drag_resampled = y_drag[::step_sz].tolist()
        
        # Ensure exact end point is added
        if len(x_drag) > 0:
            x_drag_resampled.append(x_drag[-1])
            y_drag_resampled.append(y_drag[-1])

        # KPIs for drag case
        range_drag = float(x_drag[-1])
        h_max_drag = float(np.max(y_drag))
        t_flight_drag = float(t)
        v_final_drag = float(math.sqrt(traj_arr[-1, 2]**2 + traj_arr[-1, 3]**2))

        return {
            "x_vacuum": x_vac.tolist(),
            "y_vacuum": y_vac.tolist(),
            "x_drag": x_drag_resampled,
            "y_drag": y_drag_resampled,
            "stats": {
                "range_vacuum_m": float(range_vac),
                "height_vacuum_m": float(h_max_vac),
                "time_vacuum_s": float(t_flight_vac),
                "range_drag_m": range_drag,
                "height_drag_m": h_max_drag,
                "time_drag_s": t_flight_drag,
                "final_velocity_drag_m_s": v_final_drag,
            }
        }
