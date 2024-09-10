function [force] = force_calculator_script(v_, v0_, mass_, stepSize_)
  if v0_ == 0
    force = 0;
  else
    acceleration =  (v_ - v0_) / stepSize_;
    force = mass_* acceleration;
  end
end