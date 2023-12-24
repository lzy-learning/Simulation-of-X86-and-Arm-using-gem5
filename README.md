# Simulation-of-X86-and-Arm-using-gem5
Recurrent of paper: Simulation of ARM and x86 Microprocessors Using In-order and Out-of-order CPU Models with Gem5 Simulator 



- environmental requirements

  ```shell
  gem5
  numpy
  matplotlib
  ```

- how to run the program

  ```shell
  cd ~/gem5-stable/configs
  
  git clone https://github.com/lzy-learning/Simulation-of-X86-and-Arm-using-gem5.git
  
  cd Simulation-of-X86-and-Arm-using-gem5
  
  # run the simulation, it may take a long time
  python3 
  
  # analysis the result
  python3
  ```

  



> Note that simulation results may vary with different versions of Gem5, and it is also important to note that lower versions of Gem5 may require to enable the In-order CPU model for x86 processor.  Please refer to Appendix A of the original paper for concrete method.
